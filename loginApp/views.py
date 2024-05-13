import mimetypes
from urllib.parse import urlparse

import boto3
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404

from mysite import settings
from .forms import ComplaintForm
from .models import Complaint, ComplaintFile
from .models import Thread, Post

@login_required
def dashboard(request):
    complaints = Complaint.objects.filter(
        user=request.user) if not (request.user.groups.filter(
        name='Site Admin').exists()) else Complaint.objects.all()

    for complaint in complaints:
        complaint_files = ComplaintFile.objects.filter(complaint=complaint)
        for complaint_file in complaint_files:
            mime_type, _ = mimetypes.guess_type(complaint_file.file.url)
            complaint_file.is_image = mime_type.startswith('image/') if mime_type else False
            complaint_file.is_pdf = 'application/pdf' == mime_type if mime_type else False
            complaint_file.is_text = 'text/plain' == mime_type if mime_type else False
        complaint.files_info = complaint_files

    userType = 'loginApp/AdminDashboard.html' if request.user.groups.filter(
        name='Site Admin').exists() else 'loginApp/UserDashboard.html'
    return render(request, userType, {'complaints': complaints})

@login_required
def complaint_form(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()

            files = request.FILES.getlist('upload')
            for file in files:
                ComplaintFile.objects.create(complaint=complaint, file=file)

            if request.user.email:
                subject = "Complaint Submission Confirmed"
                message = f"Dear {request.user.username}, \n\nYour complaint has been successfully submitted and is now under review. \n\nComplaint details:\n- Name: {complaint.name}\n- Location: {complaint.location}\n- Description: {complaint.description}\n\nWe will notify you of any updates regarding your complaint status.\n\nThank you for bringing this to our attention."

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [request.user.email],
                fail_silently=False,
            )

            return redirect('complaint_success')
    else:
        form = ComplaintForm()
    return render(request, 'loginApp/complaint_form.html', {'form': form})


def anonymous_complaint_view(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.name = 'Anonymous'
            complaint.user = None
            complaint.is_anonymous = True
            complaint.save()

            files = request.FILES.getlist('upload')
            for file in files:
                ComplaintFile.objects.create(complaint=complaint, file=file)

            return render(request, 'loginApp/complaint_success_anon.html')
    else:
        # when it is a GET request
        form = ComplaintForm(initial={'name': 'Anonymous'})
        form.fields['name'].widget.attrs['readonly'] = True
    return render(request, 'loginApp/anonymous_complaint_form.html', {'form': form})


@login_required
def complaint_success(request):
    return render(request, 'loginApp/complaint_success.html')

@login_required
def deletecomplaintcommon(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.user != complaint.user:
        messages.error(request, "You do not have permission to delete this complaint.")
        return HttpResponseRedirect(reverse('dashboard'))

    if request.method == 'POST':
        if hasattr(complaint, 'upload') and complaint.upload:
            s3 = boto3.client('s3')
            s3_url = complaint.upload.url
            parsed_url = urlparse(s3_url)
            s3_key = parsed_url.path[1:]
            try:
                s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
            except Exception as e:
                messages.error(request, "Error deleting file from storage.")
                return HttpResponseRedirect(reverse('dashboard'))
        complaint.files.all().delete()
        complaint.delete()
        messages.success(request, "Complaint deleted successfully.")
        return HttpResponseRedirect(reverse('dashboard'))
    return render(request, 'loginApp/delete_confirmation.html', {'complaint': complaint})


@login_required
def editcomplaintcommon(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            saved_complaint = form.save()

            files_to_delete = request.POST.getlist('delete_files')
            if files_to_delete:
                ComplaintFile.objects.filter(id__in=files_to_delete).delete()

            files = request.FILES.getlist('upload')
            for file in files:
                ComplaintFile.objects.create(complaint=saved_complaint, file=file)
            return redirect('complaint_success')
    else:
        form = ComplaintForm(instance=complaint)

    return render(request, 'loginApp/edit_form.html', {'form': form, 'complaint': complaint})

class ThreadListView(ListView):
    template_name = "thread_list.html"
    context_object_name = "list"

    def get_queryset(self):
        return Thread.objects.order_by("-created_at")


class ThreadDetailView(DetailView):
    model = Thread


class CreateThreadView(CreateView):
    model = Thread
    fields = ['title']
    success_url = reverse_lazy('thread_list')


class CreatePostView(CreateView):
    model = Post
    fields = ['content']

    def form_valid(self, form):
        form.instance.thread_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('thread_detail', kwargs={'pk': self.kwargs['pk']})


def handle_complaint_click(request, complaint_id):
    complaint = Complaint.objects.filter(id=complaint_id).first()
    if request.method == 'POST':
        if complaint:
            status = request.POST.get('status')
            review = request.POST.get('review')
            if status in dict(Complaint.STATUS_CHOICES):
                previous_status = complaint.status

                complaint.status = status
                if status == 'reviewed' or status == 'in_progress':
                    complaint.review = review
                complaint.save()

                if previous_status != status and complaint.user and complaint.user.email:
                    subject = "Complaint Update"
                    message = f'Dear {complaint.user},\n\nYour complaint status has changed to: {complaint.get_status_display()}.\n\nComplaint details:\n- Name: {complaint.name}\n- Location: {complaint.location}\n- Description: {complaint.description}\n\n'
                    if status == 'reviewed':
                        message += f'Review notes:\n{review}\n\nWe appreciate your patience as we reviewed your complaint. Thank you for bringing this issue to our attention. Your input is invaluable to us in ensuring a safe and comfortable environment'
                    else:
                        message += f'Your complaint is now being actively addressed.\n\nWe are committed to resolving it as swiftly as possible. You will receive further updates as we progress. Please feel free to reach out if you have any questions or need additional assistance in the meantime.'

                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [complaint.user.email],
                        fail_silently=False,
                    )

                return render(request, 'loginApp/complaintviews.html', {'complaints': complaint})
    else: 
        if complaint:
            status = complaint.status
            if status == 'notreviewed':
                complaint.status = 'in_progress'  
                complaint.save()
                if complaint.user and complaint.user.email:
                    subject = "Complaint Update"
                    message = f'Dear {complaint.user},\n\nYour complaint status has changed to: {complaint.get_status_display()}.\n\nComplaint details:\n- Name: {complaint.name}\n- Location: {complaint.location}\n- Description: {complaint.description}\n\n'
                    message += f'Your complaint is now being actively addressed.\n\nWe are committed to resolving it as swiftly as possible. You will receive further updates as we progress. Please feel free to reach out if you have any questions or need additional assistance in the meantime.'

                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [complaint.user.email],
                        fail_silently=False,
                    )
    return render(request, 'loginApp/complaintviews.html', {'complaints': complaint})


def about(request):
    return render(request, 'loginApp/about.html')

@login_required
def delete_all_complaints(request):
    if not request.user.groups.filter(name='Site Admin').exists():
        messages.error(request, "You do not have permission to perform this action.")
        return HttpResponseRedirect(reverse('dashboard'))

    if request.method == 'POST':
        Complaint.objects.all().delete()
        messages.success(request, "All complaints have been deleted successfully.")
        return HttpResponseRedirect(reverse('dashboard'))

    return render(request, 'loginApp/delete_all_confirmation.html')
