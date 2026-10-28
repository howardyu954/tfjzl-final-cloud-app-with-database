from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Lesson, Enrollment, Question, Choice, Submission

def popular_course_list(request):
    context = {}
    if request.method == 'GET':
        course_list = Course.objects.order_by('-total_enrollment')[:10]
        context['course_list'] = course_list
        return render(request, 'onlinecourse/course_list.html', context)

def enroll(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        user = request.user
        if user.is_authenticated:
            enrollment, created = Enrollment.objects.get_or_create(user=user, course=course)
            if created:
                course.total_enrollment += 1
                course.save()
            return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))
        else:
            return HttpResponseRedirect(reverse(viewname='onlinecourse:login'))

def course_details(request, course_id):
    context = {}
    if request.method == 'GET':
        course = get_object_or_404(Course, pk=course_id)
        context['course'] = course
        return render(request, 'onlinecourse/course_details_bootstrap.html', context)

def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    
    for key, value in request.POST.items():
        if key.startswith('choice_'):
            choice = get_object_or_404(Choice, id=int(value))
            submission.choices.add(choice)
    submission.save()
    return HttpResponseRedirect(reverse('onlinecourse:show_exam_result', args=(course.id, submission.id)))

def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    total_score = 0
    possible_score = 0
    selected_ids = [c.id for c in submission.choices.all()]
    
    for question in course.question_set.all():
        possible_score += question.grade
        if question.is_get_score(selected_ids):
            total_score += question.grade
            
    grade = int((total_score / possible_score) * 100) if possible_score > 0 else 0
    
    context['course'] = course
    context['grade'] = grade
    context['choices'] = submission.choices.all()
    context['selected_ids'] = selected_ids
    context['possible_score'] = possible_score
    context['is_passed'] = grade >= 80
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

def registration_request(request):
    context = {}
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        try:
            User.objects.get(username=username)
            context['error'] = 'User already exists.'
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
        except Exception:
            user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
            login(request, user)
            return redirect('onlinecourse:index')
    return render(request, 'onlinecourse/user_registration_bootstrap.html', context)

def login_request(request):
    context = {}
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['error'] = 'Invalid username or password.'
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    return render(request, 'onlinecourse/user_login_bootstrap.html', context)

def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')
