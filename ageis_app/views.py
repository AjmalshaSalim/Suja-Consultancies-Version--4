import random
from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, HttpResponseServerError
from django.contrib.auth.models import User,auth
from django.contrib import messages
from iso8601 import parse_date
import requests
from ageis_app.models import *
from ageis_app.forms import *
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Count
from django.views.generic import ListView
from django.db.models import F
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login
from datetime import datetime, timedelta 
from django.core.exceptions import PermissionDenied


def error_page(request):
    return render(request, 'error.html', {})


def index(request):
    try:

        recent_jobs = []
        whatsapp = None
        extended_user = None

        if request.user.is_authenticated:
            user = request.user
            recent_jobs = RecentlySearchedJobs.objects.filter(user=user).order_by('-search_date')

            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()
                if not extended_user.phone:
                    whatsapp = 'email'
        
        job_posted_count = Jobs.objects.count()
        applied_jobs_count = AppliedJobs.objects.count()
        company_count = Clients.objects.count()
        members_count = ExtendedUserModel.objects.count()
        companies = Clients.objects.all()
        jobs = Jobs.objects.all().order_by('job_post_date')[:4]
        job_category = JobCategories.objects.all()
        testimonial = Testimonials.objects.all()

        category_data = {}
        for category in job_category:
            category_data[category.id] = {
                'id': category.id,
                'name': category.name,
                'image_url': category.image.url if category.image else None,
                'count': Jobs.objects.filter(job_category=category).count()
            }

        development_count = Jobs.objects.filter(job_category__id=7).count()
        accounting_finance_count = Jobs.objects.filter(job_category__id=1).count()
        internship_count = Jobs.objects.filter(job_category__id=2).count()
        automotive_count = Jobs.objects.filter(job_category__id=3).count()
        marketing_count = Jobs.objects.filter(job_category__id=4).count()
        human_resource_count = Jobs.objects.filter(job_category__id=5).count()
        customer_service_count = Jobs.objects.filter(job_category__id=6).count()
        project_management_count = Jobs.objects.filter(job_category__id=8).count()
        design_count = Jobs.objects.filter(job_category__id=9).count()

        most_applied_jobs = Jobs.objects.filter(application_count__gt=0).order_by('-application_count')[:20]

        context = {
            'companies': companies,
            'jobs': jobs,
            'job_posted_count': job_posted_count,
            'applied_jobs_count': applied_jobs_count,
            'company_count': company_count,
            'members_count': members_count,
            'testimonial': testimonial,
            'category_data': category_data,
            'development_count': development_count,
            'accounting_finance_count': accounting_finance_count,
            'internship_count': internship_count,
            'automotive_count': automotive_count,
            'marketing_count': marketing_count,
            'human_resource_count': human_resource_count,
            'customer_service_count': customer_service_count,
            'project_management_count': project_management_count,
            'design_count': design_count,
            'most_applied_jobs': most_applied_jobs,
            'recent_jobs': recent_jobs,
            'whatsapp': whatsapp,
            'extended_user': extended_user,
        }
        
        return render(request, 'index.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Render an error page with the exception message
        context = {'error_message': str(e)}
        return render(request, 'error.html', context)


@login_required
def submit_whatsapp_number(request):
    try:
        if request.method == 'POST':
            whatsapp_number = request.POST.get('whatsapp_number')

            if whatsapp_number and whatsapp_number.isdigit() and len(whatsapp_number) == 10:
                user_profile, created = ExtendedUserModel.objects.get_or_create(user=request.user)
                user_profile.phone = whatsapp_number
                user_profile.save()
                messages.success(request, 'Your WhatsApp number has been saved.')
            else:
                messages.error(request, 'Please enter a valid WhatsApp number.')

        return redirect('ageis_app:index')  

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while saving your WhatsApp number. Please try again later.")
        return redirect('ageis_app:error_page')  # Redirect to a custom error page if desired
    

def jobs_by_application_count(request):
    try:
        # Fetch jobs with application count greater than 0, ordered by application count
        jobs = Jobs.objects.filter(application_count__gt=0).order_by('-application_count')
        return render(request, 'jobsfrontend.html', {'jobs': jobs})

    except Exception as e:
        # Log the exception (optional)
        print(f"An error occurred: {e}")

        # Prepare an error message for the user
        error_message = "An unexpected error occurred while retrieving job data. Please try again later."
        
        # Pass the error message to the context and render the error template
        context = {'error_message': error_message}
        return render(request, 'error.html', context)
    
@login_required
def recently_searched_jobs(request):
    try:
        user = request.user

        # Fetch recent searches
        recent_searches = RecentlySearchedJobs.objects.filter(user=user).order_by('-search_date')

        # Extract job objects from recent searches
        recent_jobs = [search.job for search in recent_searches]

        context = {
            'jobs': recent_jobs
        }
        return render(request, 'jobsfrontend.html', context)
    
    except RecentlySearchedJobs.DoesNotExist:
        # Handle the case where there are no recent searches
        messages.error(request, "No recent searches found.")
        return redirect('index')  # Redirect to a safe page, e.g., home page
    
    except Exception as e:
        # Log the exception and show a generic error message
        print(f"An error occurred: {e}")
        context = {'error_message': str(e)}
        return render(request, 'error.html', context)


# def admin_registration(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         password2 = request.POST.get('password2')
#         if password == password2:
#             if User.objects.filter(username = username).exists():
#                 messages.error(request,'Username alredy exists')
#                 return redirect('ageis_app:admin_registration')
#             elif User.objects.filter(email = email).exists():
#                 messages.error(request,'Email alredy exists')
#                 return redirect('ageis_app:admin_registration')
#             else:
#                 User.objects.create_superuser(username=username,email=email,password=password)
#                 messages.success(request,'User created..')
#                 return redirect('ageis_app:login')
#         else:
#             messages.error(request,'Password Not Match')
#             return redirect('ageis_app:admin_registration')
#     return render(request,'admin-register.html')

def send_otp(phone_num, otp):
    print("Reached OTP sent helper")
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = f'variables_values={otp}&route=otp&language=english&numbers={phone_num}'
    headers = {
        'authorization': "mEgP0Z5wnldKSerOu1GW8qUbVctH3jkYaM7QCI4Jzp69XNT2ALFmiofRb467D0rSOWVB3qp8J5HYeIvt",
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
    }
    
    try:
        # Make the POST request
        response = requests.post(url, data=payload, headers=headers)
        
        # Check if the response status code is 200 OK
        response.raise_for_status()

        # Parse the response JSON data
        response_data = response.json()
        
        # Check if the OTP was sent successfully
        if response_data.get("return") == True:
            print("OTP sent successfully")
            return True
        else:
            error_message = response_data.get('message', 'Unknown error')
            print(f"Failed to send OTP: {error_message}")
            return False

    except requests.exceptions.HTTPError as http_err:
        # Handle HTTP errors
        print(f"HTTP error occurred: {http_err}")
        return False
    except requests.exceptions.RequestException as req_err:
        # Handle other request-related errors
        print(f"Request error occurred: {req_err}")
        return False
    except Exception as e:
        # Handle any other exceptions
        print(f"An unexpected error occurred: {e}")
        return False

def generate_otp():
    return str(random.randint(1000, 9999))


def email_submission(request):
    try:
        if request.method == 'POST':
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            # Generate OTP
            otp = generate_otp()

            if email:
                # Save OTP to the session for email
                request.session['email'] = email
                request.session['otp'] = otp

                # Send OTP to the email
                try:
                    send_mail(
                        'Your OTP Code',
                        f'Your OTP code is: {otp}',
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, 'OTP has been sent to your email.')
                except Exception as e:
                    # Log the exception or handle it as needed
                    print(f"Failed to send email: {e}")
                    messages.error(request, 'Failed to send OTP to your email. Please try again later.')
            
            elif phone:
                # Save OTP to the session for phone
                request.session['phone'] = phone
                request.session['otp'] = otp

                # Send OTP to the phone number
                try:
                    send_otp(phone, otp)
                    messages.success(request, 'OTP has been sent to your phone number.')
                except Exception as e:
                    # Log the exception or handle it as needed
                    print(f"Failed to send OTP to phone: {e}")
                    messages.error(request, 'Failed to send OTP to your phone number. Please try again later.')
            
            return redirect('ageis_app:otp_verification')
        
        return render(request, 'email_login.html')

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Render an error page with the exception message
        context = {'error_message': str(e)}
        return render(request, 'error.html', context)


from django.contrib.auth import authenticate, login as auth_login

def otp_verification(request):
    try:
        if request.method == 'POST':
            # Retrieve the phone number and email from the session
            phone_num = request.session.get('phone')
            email = request.session.get('email')
            
            # Retrieve the entered OTP from the request
            otp_entered = request.POST.get('otp')
            
            # Retrieve the saved OTP from the session
            otp_saved = request.session.get('otp')

            print('otp_entered:', otp_entered)
            print('otp_saved:', otp_saved)

            if otp_saved and otp_entered == otp_saved:
                # Handle Phone Number Verification
                if phone_num:
                    # Check if a user with this phone number already exists
                    if ExtendedUserModel.objects.filter(phone=phone_num).exists():
                        user = ExtendedUserModel.objects.get(phone=phone_num).user
                    else:
                        # Create a new user if they do not exist
                        username = f"user_{phone_num[-4:]}"  # Simple username generation based on phone number
                        user = User.objects.create_user(username=username, password='12345678')
                        ExtendedUserModel.objects.create(user=user, phone=phone_num)
                
                # Handle Email Verification
                elif email:
                    # Check if a user with this email already exists
                    if User.objects.filter(email=email).exists():
                        user = User.objects.get(email=email)
                    else:
                        # Create a new user if they do not exist
                        username = email.split('@')[0]  # Simple username generation based on email
                        user = User.objects.create_user(username=username, email=email, password='12345678')
                        ExtendedUserModel.objects.create(user=user)
                
                # If neither phone number nor email is provided, raise an error
                else:
                    messages.error(request, "No phone number or email provided for verification.")
                    return redirect('ageis_app:otp_verification')

                # Authenticate the user
                user = authenticate(username=user.username, password='12345678')
                if user is not None:
                    auth_login(request, user)  # Log the user in
                    messages.success(request, 'OTP verified and logged in successfully.')
                    
                    # Clear the session data
                    request.session.pop('email', None)
                    request.session.pop('phone', None)
                    request.session.pop('otp', None)
                    
                    return redirect('ageis_app:index')  # Redirect to home or another page
                else:
                    messages.error(request, 'Authentication failed.')
            else:
                messages.error(request, 'Invalid OTP or OTP has expired.')
        
        return render(request, 'otp_verification.html')

    except Exception as e:
        # Log the exception
        print(f"An error occurred: {e}")

        # Clear session data in case of error
        request.session.pop('email', None)
        request.session.pop('phone', None)
        request.session.pop('otp', None)
        
        # Display error message
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return redirect('ageis_app:otp_verification')



def resend_otp(request):
    try:
        phone = request.session.get('phone')
        email = request.session.get('email')

        if not phone and not email:
            messages.error(request, 'No contact information found to send OTP.')
            return redirect('ageis_app:otp_verification')

        otp = generate_otp()

        if email:
            request.session['otp'] = otp
            try:
                send_mail(
                    'Your OTP Code',
                    f'Your new OTP code is: {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'A new OTP has been sent to your email.')
            except Exception as e:
                messages.error(request, f'Failed to send OTP to email: {e}')
                print(f"Email sending error: {e}")

        elif phone:
            request.session['otp'] = otp
            try:
                send_otp(phone, otp)
                messages.success(request, 'A new OTP has been sent to your phone number.')
            except Exception as e:
                messages.error(request, f'Failed to send OTP to phone: {e}')
                print(f"SMS sending error: {e}")

        return redirect('ageis_app:otp_verification')

    except Exception as e:
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        print(f"Unexpected error: {e}")
        return redirect('ageis_app:otp_verification')



# def user_registration(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         email = request.POST.get('email')
#         phone = request.POST.get('phone')
#         cv = request.FILES.get('resume')
#         # print('CV',cv)
#         password = request.POST.get('password')
#         password2 = request.POST.get('password2')
#         if password == password2:
#             if User.objects.filter(username = username).exists():
#                 messages.error(request,'Username alredy exists')
#                 return redirect('ageis_app:user_registration')
#             elif User.objects.filter(email = email).exists():
#                 messages.error(request,'Email alredy exists')
#                 return redirect('ageis_app:user_registration')
#             else:
#                 user = User.objects.create_user(username=username,first_name=first_name,last_name=last_name,email=email,password=password)
#                 extendeduser = ExtendedUserModel(user = user, phone = phone, cv = cv)
#                 extendeduser.save()
#                 messages.success(request,'User created..')
#                 return redirect('ageis_app:login')
#         else:
#             messages.error(request,'Password Not Match')
#             return redirect('ageis_app:user_registration')
#     return render(request,'user-register.html')

# def edit_user(request, user_id):
#     if request.method == 'POST':

#         print('Form Data:', request.POST)
#         print('Degrees:', request.POST.getlist('degree[]'))
#         print('Institutions:', request.POST.getlist('institution[]'))
#         print('Completion Years:', request.POST.getlist('completion_year[]'))
      



#         user = get_object_or_404(User, id=user_id)
#         extended_user = get_object_or_404(ExtendedUserModel, user=user)
        
#         # Update User fields
#         user.first_name = request.POST.get('first_name')
#         user.last_name = request.POST.get('last_name')
#         user.email = request.POST.get('email')
#         user.save()
#         # Update ExtendedUserModel fields
#         extended_user.phone = request.POST.get('phone')
#         extended_user.location = request.POST.get('location')
#         # Handle the CV upload
#         if 'cv' in request.FILES:
#             extended_user.cv = request.FILES['cv']
#         extended_user.save()
        
#         # Update Skills
#         skills = request.POST.get('skills', '')
#         skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
#         for skill in skills_list:
#             Skills.objects.create(user=extended_user, skill=skill)


#         # Update Qualifications
#         degrees = request.POST.getlist('degree[]')
#         institutions = request.POST.getlist('institution[]')
#         completion_years = request.POST.getlist('completion_year[]')
#         print("degrees",degrees,"institutions",institutions,"completion_years",completion_years)
#         processed_qualification_ids = []

#         for degree, institution, year in zip(degrees, institutions, completion_years):
#             if degree and institution and year:
#                 qualification, created = Qualification.objects.update_or_create(
#                     user=extended_user,
#                     degree=degree,
#                     institution=institution,
#                     defaults={'completion_year': int(year)}
#                 )
#                 processed_qualification_ids.append(qualification.id)


#         # Process Experiences
#         companies = request.POST.getlist('company[]')
#         positions = request.POST.getlist('position[]')
#         start_dates = request.POST.getlist('start_date[]')
#         end_dates = request.POST.getlist('end_date[]')
#         descriptions = request.POST.getlist('description[]')

#         print("companies",companies)
#         # Track processed experience IDs to avoid duplications
#         processed_experience_ids = []

#         for company, position, start_date, end_date, description in zip(companies, positions, start_dates, end_dates, descriptions):
#             if company and position and start_date:
#                 # Use a more specific filter to ensure uniqueness
#                 experience = Experience.objects.filter(
#                     user=extended_user,
#                     company=company,
#                     position=position,
#                     start_date=start_date
#                 ).first()
                
#                 if experience:
#                     # Update the existing experience
#                     experience.end_date = end_date if end_date else None
#                     experience.description = description
#                     experience.save()
#                 else:
#                     # Create a new experience
#                     Experience.objects.create(
#                         user=extended_user,
#                         company=company,
#                         position=position,
#                         start_date=start_date,
#                         end_date=end_date if end_date else None,
#                         description=description
#                     )

#         # Optionally, delete experiences that were not processed
#         # Experience.objects.filter(user=extended_user).exclude(id__in=processed_experience_ids).delete()
#         messages.success(request, 'User information updated successfully.')
#         return redirect('ageis_app:user_management')
    
#     return redirect('/')


def edit_user(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            extended_user = get_object_or_404(ExtendedUserModel, user=user)

            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()


            extended_user.phone = request.POST.get('phone')
            extended_user.location = request.POST.get('location')
            extended_user.gender = request.POST.get('gender')
            extended_user.country = request.POST.get('country')
            extended_user.state = request.POST.get('state')
            extended_user.district = request.POST.get('district')
            extended_user.relocate = request.POST.get('relocate_add') == 'on'
            extended_user.dob = request.POST.get('dob')
            extended_user.address = request.POST.get('address')
            extended_user.currently_working = request.POST.get('currently_working') == 'on'
            extended_user.current_company = request.POST.get('current_company')
            extended_user.current_start_date = request.POST.get('current_start_date')
            extended_user.position = request.POST.get('current_position')
            extended_user.discription = request.POST.get('discription')
            extended_user.currently_working = 'currently_working' in request.POST
        
            if extended_user.currently_working:
                extended_user.current_company = request.POST.get('current_company')
                extended_user.current_start_date = request.POST.get('current_start_date')
                extended_user.current_position = request.POST.get('current_position')
                extended_user.discription = request.POST.get('discription')
            else:
                # Clear current job fields if not currently working
                extended_user.current_company = ''
                extended_user.current_start_date = None
                extended_user.current_position = ''
                extended_user.discription = ''

            if 'cv' in request.FILES:
                extended_user.cv = request.FILES['cv']

            if 'profile_photo' in request.FILES:
                extended_user.profile_photo = request.FILES['profile_photo']

            extended_user.save()


            
            skills = request.POST.get('skills', '')
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            for skill in skills_list:
                if not Skills.objects.filter(user=extended_user, skill=skill).exists():
                    Skills.objects.create(user=extended_user, skill=skill)

            
            Qualification.objects.filter(user=extended_user).delete() 
            degrees = request.POST.getlist('degree[]')
            institutions = request.POST.getlist('institution[]')
            completion_years = request.POST.getlist('completion_year[]')
            for degree, institution, year in zip(degrees, institutions, completion_years):
                if degree and institution and year:
                    Qualification.objects.create(
                        user=extended_user,
                        degree=degree,
                        institution=institution,
                        completion_year=int(year)
                    )


            Experience.objects.filter(user=extended_user).delete()  
            companies = request.POST.getlist('company[]')
            positions = request.POST.getlist('position[]')
            start_dates = request.POST.getlist('start_date[]')
            end_dates = request.POST.getlist('end_date[]')
            descriptions = request.POST.getlist('description[]')
            for company, position, start_date, end_date, description in zip(companies, positions, start_dates, end_dates, descriptions):
                if company and position and start_date:
                    Experience.objects.create(
                        user=extended_user,
                        company=company,
                        position=position,
                        start_date=start_date,
                        end_date=end_date if end_date else None,
                        description=description
                    )

           
            preferred_job_titles = request.POST.get('preferred_job_titles', '')
            preferred_job_titles_list = [title.strip() for title in preferred_job_titles.split(',') if title.strip()]
            for title in preferred_job_titles_list:
                if not PreferredJobTitle.objects.filter(user=user, job_title=title).exists():
                    PreferredJobTitle.objects.create(user=user, job_title=title)

            
            languages = request.POST.get('languages', '')
            languages_list = [language.strip() for language in languages.split(',') if language.strip()]
            for language in languages_list:
                if not Language.objects.filter(user=user, language=language).exists():
                    Language.objects.create(user=user, language=language)

            messages.success(request, 'User information updated successfully.')
            return redirect('ageis_app:user_management')
        
        except Exception as e:

            print(f"An error occurred: {e}")

            messages.error(request, f"An unexpected error occurred: {e}")
            return render(request, 'error.html', {'error_message': str(e)})
        
    return redirect('/')



def create_user(request):
    if request.method == 'POST':
        try:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            cv = request.FILES.get('cv')
            profile_photo = request.FILES.get('profile_photo')
            dob = request.POST.get('dob')
            gender = request.POST.get('gender')
            country = request.POST.get('country')
            state = request.POST.get('state')
            district = request.POST.get('district')
            discription = request.POST.get('discription', '')
            currently_working = request.POST.get('currently_working') == 'on'
            relocate_add = request.POST.get('relocate_add') == 'on'
            current_company = request.POST.get('current_company', '')
            current_start_date = request.POST.get('current_start_date')
            current_position = request.POST.get('current_position', '')
            address = request.POST.get('address', '')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('ageis_app:create_user')

            username = email.split('@')[0]
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email)
            extended_user = ExtendedUserModel(
                user=user,
                phone=phone,
                location=location,
                profile_photo = profile_photo,
                country=country,
                state=state,
                district=district,
                relocate = relocate_add,
                cv=cv,
                dob=dob,
                address=address,
                gender=gender,
                currently_working=currently_working,
                current_company=current_company,
                current_start_date=current_start_date if current_start_date else None,
                position=current_position,
                discription = discription,
                created_by = request.user

            )
            extended_user.save()

            # Handle Skills
            skills = request.POST.get('skills', '')
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            for skill in skills_list:
                Skills.objects.create(user=extended_user, skill=skill)

            # Handle Qualifications
            degrees = request.POST.getlist('degree[]')
            institutions = request.POST.getlist('institution[]')
            completion_years = request.POST.getlist('completion_year[]')
            for degree, institution, year in zip(degrees, institutions, completion_years):
                if degree and institution and year:
                    Qualification.objects.create(
                        user=extended_user,
                        degree=degree,
                        institution=institution,
                        completion_year=int(year)
                    )

            # Handle Experience
            companies = request.POST.getlist('company[]')
            positions = request.POST.getlist('position[]')
            start_dates = request.POST.getlist('start_date[]')
            end_dates = request.POST.getlist('end_date[]')
            descriptions = request.POST.getlist('description[]')
            for company, position, start_date, end_date, description in zip(companies, positions, start_dates, end_dates, descriptions):
                if company and position and start_date:
                    Experience.objects.create(
                        user=extended_user,
                        company=company,
                        position=position,
                        start_date=start_date,
                        end_date=end_date if end_date else None,
                        description=description
                    )
            # Handle Preferred Job Titles
            preferred_job_titles = request.POST.get('preferred_job_titles', '')
            preferred_job_titles_list = [title.strip() for title in preferred_job_titles.split(',') if title.strip()]
            for title in preferred_job_titles_list:
                PreferredJobTitle.objects.create(user=extended_user.user, job_title=title)

            # Handle Languages
            languages = request.POST.get('languages', '')
            languages_list = [language.strip() for language in languages.split(',') if language.strip()]
            for language in languages_list:
                Language.objects.create(user=extended_user.user, language=language)




            messages.success(request, 'User created successfully.')
            return redirect('ageis_app:user_management')  # Replace with your actual user list view
        
        except Exception as e:
            # Log the exception or handle it as needed
            print(f"An error occurred: {e}")
            # Add an error message to be displayed on the error page
            messages.error(request, f"An unexpected error occurred: {e}")
            return render(request, 'error.html', {'error_message': str(e)})
        
    return redirect('/')  # Handle non-POST requests appropriately

from django.core.exceptions import ObjectDoesNotExist
def login(request):
    try:
        if 'username' in request.session:
            print("username in session already")
            return redirect('ageis_app:dashboard')

        if request.method == 'POST':
            username_or_email = request.POST.get('username_or_email')
            password = request.POST.get('password')

            # Try to authenticate the user
            user = auth.authenticate(request, username=username_or_email, password=password)
            if user is not None:
                print("Request is POST and user is not None")
                auth.login(request, user)
                request.session['username'] = username_or_email

                if user.is_superuser:
                    return redirect('ageis_app:dashboard')
                else:
                    print('User')
                    return redirect('ageis_app:dashboard')
            else:
                print("Request is POST and user None")
                messages.error(request, 'Invalid credentials. Please check your username or password and try again.')
                return render(request, 'login.html')  # Stay on the login page
        return render(request, 'login.html')

    except ObjectDoesNotExist as e:
        # Handle specific exception if needed
        print(f"ObjectDoesNotExist error: {e}")
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return render(request, 'error.html', {'error_message': str(e)})
    
    except Exception as e:
        # Handle any other exception
        print(f"An error occurred: {e}")
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return render(request, 'error.html', {'error_message': str(e)})


def logout(request):
    try:
        if 'username' in request.session:
            request.session.flush()
        messages.success(request, "You have been logged out successfully.")
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred during logout: {e}")
        messages.error(request, "An unexpected error occurred while logging out. Please try again.")
    return redirect('ageis_app:dashboard')

from django.contrib.auth import logout as auth_logout
def user_logout(request):
    try:
        # Use Django's built-in logout function to log the user out
        auth_logout(request)
        messages.success(request, "You have been logged out successfully.")
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred during logout: {e}")
        messages.error(request, "An unexpected error occurred while logging out. Please try again.")
    return redirect('ageis_app:index')

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

# def forgot_password(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         if ExtendedUserModel.objects.filter(user__email=email).exists():
#             user = ExtendedUserModel.objects.get(user__email=email)
#             user = User.objects.get(email=email)
#             token_generator = PasswordResetTokenGenerator()
#             token = token_generator.make_token(user)
#             uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
#             reset_link = request.build_absolute_uri(
#                 reverse('ageis_app:reset_password', kwargs={'uidb64': uidb64, 'token': token}))
#             send_mail(
#                 'Password Reset Link',
#                 f'Please click on this link to reset your password: {reset_link}',
#                 settings.EMAIL_HOST_USER,
#                 [email],
#                 fail_silently=False,
#             )
#             messages.success(request, 'Password reset link has been sent to your email.')
#         else:
#             messages.error(request, 'Email does not exist.')
#     return render(request,'forgot-password.html')



# def reset_password(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None

#     if user is not None and PasswordResetTokenGenerator().check_token(user, token):
#         if request.method == 'POST':
#             if request.POST.get('password') == request.POST.get('password2'):
#                 password = request.POST.get('password')
#                 print(password)
#                 user.set_password(password)
#                 user.save()
#                 messages.success(request, 'Password has been reset.')
#                 return redirect('ageis_app:login')
#             else:
#                 messages.error(request,'Password not matching')
#                 print('password not matching')
#                 reset_password_url = reverse('ageis_app:reset_password', args=[uid, token])
#                 return redirect(reset_password_url)
#         else:
            
#             return render(request, 'reset-password.html')
#     else:
#         messages.error(request, 'Invalid reset link.')
#         return redirect('ageis_app:login')






@login_required(login_url='ageis_app:adminlogin')
def dashboard(request):
    try:
        user_type = request.user.extenedusermodel.user_type
        is_owner = user_type == 'owner'
        if user_type in ['owner', 'manager']:

            user_count = ExtendedUserModel.objects.filter(user_type='user').count()

            client_count = Clients.objects.all().count()
            jobs_count = Jobs.objects.all().count()
            applied_jobs_count = AppliedJobs.objects.all().count()
            if user_type == 'owner':

                context = {
                    'testimonial_count': user_count,
                    'client_count': client_count,
                    'jobs_count': jobs_count,
                    'applied_jobs_count': applied_jobs_count,
                    'is_owner': is_owner,

                }
            else:

                context = {
                    'testimonial_count': user_count,
                    'client_count': client_count,
                    'jobs_count': jobs_count,
                    'applied_jobs_count': applied_jobs_count,
                    'is_owner': is_owner
                }
            return render(request, 'dashboard.html', context)
        
        elif user_type == 'staff':

            user_count = ExtendedUserModel.objects.filter(
                user_type='user', 
                created_by=request.user
            ).count()

            jobs = Jobs.objects.filter(added_by=request.user).count()
            jobs_count = Jobs.objects.filter(added_by=request.user).count()  
            applied_jobs_count = AppliedJobs.objects.filter(applied_job=jobs).count()
            context = {
                'jobs_count': jobs_count,
                'applied_jobs_count':applied_jobs_count,
                'testimonial_count': user_count,
            }
            return render(request, 'dashboard.html', context)
        
        else:
            return HttpResponse('Access Denied..')
        
    except Exception as e:

        print(f"An error occurred: {e}")

        context = {'error_message': str(e)}
        return render(request, 'error.html', context)



@login_required(login_url='ageis_app:login')
def testimonial(request):
    try:
        if request.method == 'POST':
            form = TestimonialAddForm(request.POST, request.FILES)
            if form.is_valid():
                data = form.save(commit=False)
                data.added_by = request.user
                data.save()
                messages.success(request, 'Testimonial added successfully.')
                return redirect('ageis_app:testimonial')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = TestimonialAddForm()
        
        testimonial = Testimonials.objects.all()
        context = {
            'form': form,
            'testimonial': testimonial
        }
        return render(request, 'testimonal.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'testimonal.html', {'form': form, 'testimonial': testimonial, 'error_message': str(e)})

@login_required(login_url='ageis_app:login')
def testimonial_edit(request, update_id):
    try:
        # Fetch the testimonial object or return a 404 error if not found
        update = get_object_or_404(Testimonials, id=update_id)

        if request.method == 'POST':
            form = TestimonialAddForm(request.POST, request.FILES, instance=update)
            if form.is_valid():
                form.save()
                messages.success(request, 'Testimonial updated successfully.')
                return redirect('ageis_app:testimonial')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = TestimonialAddForm(instance=update)

        context = {
            'form': form
        }
        return render(request, 'testimonial-edit.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:testimonial')  

@login_required(login_url='ageis_app:login')
def testimonial_delete(request, delete_id):
    try:
        # Attempt to get the testimonial object
        testimonial = get_object_or_404(Testimonials, id=delete_id)
        
        # Check if the user has permission to delete this testimonial
        if testimonial.added_by != request.user:
            messages.error(request, "You do not have permission to delete this testimonial.")
            return redirect('ageis_app:testimonial')
        
        # Delete the testimonial
        testimonial.delete()
        messages.success(request, 'Testimonial deleted successfully.')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while trying to delete the testimonial. Please try again later.")
    
    return redirect('ageis_app:testimonial')


@login_required(login_url='ageis_app:login')
def client(request):
    form = ClientAddForm()
    try:
        if request.method == 'POST':
            form = ClientAddForm(request.POST, request.FILES)
            if form.is_valid():
                data = form.save(commit=False)
                data.added_by = request.user
                data.save()
                messages.success(request, 'Client added successfully.')
                return redirect('ageis_app:client')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the same page
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    clients = Clients.objects.all()
    return render(request, 'client.html', {'form': form, 'clients': clients})



@login_required(login_url='ageis_app:login')
def client_edit(request, client_id):
    try:
        # Retrieve the client instance or return a 404 error if not found
        update = get_object_or_404(Clients, id=client_id)
        
        if request.method == 'POST':
            form = ClientAddForm(request.POST, request.FILES, instance=update)
            if form.is_valid():
                form.save()
                messages.success(request, 'Client updated successfully.')
                return redirect('ageis_app:client')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = ClientAddForm(instance=update)
        
        context = {
            'form': form
        }
        return render(request, 'editclient.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the page
        messages.error(request, "An unexpected error occurred while updating the client. Please try again later.")
        # Ensure the form is still available for rendering
        form = ClientAddForm(instance=update) if 'update' in locals() else ClientAddForm()
        return render(request, 'editclient.html', {'form': form})


@login_required(login_url='ageis_app:login')
def client_delete(request, client_id):
    try:
        # Use get_object_or_404 to handle the case where the client does not exist
        client = get_object_or_404(Clients, id=client_id)
        client.delete()
        messages.success(request, 'Client deleted successfully.')
    except Clients.DoesNotExist:
        # Handle the case where the client does not exist
        messages.error(request, 'Client not found.')
    except Exception as e:
        # Log the exception and handle unexpected errors
        print(f"An error occurred: {e}")
        messages.error(request, 'An unexpected error occurred. Please try again later.')

    return redirect('ageis_app:client')

@login_required(login_url='ageis_app:login')
def job_categories(request):
    try:
        if request.method == 'POST':
            form = JobCategoryAddForm(request.POST, request.FILES)  # Include request.FILES for file uploads
            if form.is_valid():
                form.save()
                messages.success(request, 'Job category added successfully.')
                return redirect('ageis_app:job_categories')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = JobCategoryAddForm()

        categories = JobCategories.objects.all()
        context = {
            'form': form,
            'categories': categories
        }
        return render(request, 'jobcategories.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'jobcategories.html', {'form': form, 'categories': categories, 'error_message': str(e)})


@login_required(login_url='ageis_app:login')
def job_categories_edit(request, update_id):
    try:
        # Retrieve the job category object by id
        update = JobCategories.objects.filter(id=update_id).first()

        if not update:
            # Handle the case where the job category is not found
            messages.error(request, 'Job category not found.')
            return redirect('ageis_app:job_categories')

        if request.method == 'POST':
            # Include request.FILES to handle file uploads
            form = JobCategoryAddForm(request.POST, request.FILES, instance=update)
            if form.is_valid():
                form.save()
                messages.success(request, 'Job category updated successfully.')
                return redirect('ageis_app:job_categories')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = JobCategoryAddForm(instance=update)

        context = {
            'form': form,
        }
        return render(request, 'jobcategories-edit.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:job_categories')


@login_required(login_url='ageis_app:login')
def job_categorie_delete(request, delete_id):
    try:
        # Fetch the category object, or raise a 404 error if not found
        categorie = get_object_or_404(JobCategories, id=delete_id)
        
        # Delete the category
        categorie.delete()
        
        # Display success message
        messages.success(request, 'Category deleted successfully.')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        
        # Display error message
        messages.error(request, "An unexpected error occurred while deleting the category. Please try again later.")
    
    # Redirect to the job categories page
    return redirect('ageis_app:job_categories')


@login_required(login_url='ageis_app:login')
def job_types(request):
    try:
        if request.method == 'POST':
            form = JobTypeAddForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Job type added successfully.')
                return redirect('ageis_app:job_types')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = JobTypeAddForm()

        jobtypes = JobType.objects.all()
        context = {
            'form': form,
            'jobtypes': jobtypes
        }
        return render(request, 'jobtypes.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'jobtypes.html', {
            'form': form,
            'jobtypes': jobtypes,
            'error_message': str(e)
        })


@login_required(login_url='ageis_app:login')
def job_type_edit(request, update_id):
    try:
        # Use get_object_or_404 to handle non-existent update_id
        update = get_object_or_404(JobType, id=update_id)

        if request.method == 'POST':
            form = JobTypeAddForm(request.POST, instance=update)
            if form.is_valid():
                form.save()
                messages.success(request, 'Job type updated successfully.')
                return redirect('ageis_app:job_types')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = JobTypeAddForm(instance=update)

        context = {
            'form': form,
        }
        return render(request, 'jobcategories-edit.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'jobcategories-edit.html', {'form': form, 'error_message': str(e)})




@login_required(login_url='ageis_app:login')
def job_type_delete(request, delete_id):
    try:
        # Attempt to retrieve the JobType object
        categorie = JobType.objects.filter(id=delete_id).first()
        
        if not categorie:
            # If the object is not found, display an error message
            messages.error(request, 'Job type not found.')
            return redirect('ageis_app:job_types')
        
        # Attempt to delete the object
        categorie.delete()
        messages.success(request, 'Job type deleted successfully.')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed
        messages.error(request, 'An unexpected error occurred while deleting the job type. Please try again later.')
    
    return redirect('ageis_app:job_types')


@login_required(login_url='ageis_app:login')
def load_states(request):
    try:
        country_id = request.GET.get('country_id')
        if not country_id:
            return JsonResponse({'error': 'Country ID is required'}, status=400)
        
        # Fetch states based on the provided country_id
        states = State.objects.filter(country=country_id).all()
        
        # If no states are found, return an empty list
        if not states.exists():
            return JsonResponse({'states': []})
        
        # Render the states options into the response
        return render(request, 'city_dropdown_list_options.html', {'states': states})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Return a JSON response with an error message
        return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)

# @login_required(login_url='ageis_app:login')
# def load_district(request):
#     try:
#         state_id = request.GET.get('state_id')  # Changed from country_id to state_id to match your context
#         if not state_id:
#             return JsonResponse({'error': 'State ID is required'}, status=400)
        
#         # Fetch districts based on the provided state_id
#         districts = district.objects.filter(state=state_id).all()
        
#         # If no districts are found, return an empty list
#         if not districts.exists():
#             return JsonResponse({'districts': []})
        
#         # Render the districts options into the response
#         return render(request, 'place_dropdown_list_options.html', {'districts': districts})

#     except Exception as e:
#         # Log the exception or handle it as needed
#         print(f"An error occurred: {e}")
#         # Return a JSON response with an error message
#         return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)

@login_required(login_url='ageis_app:login')
def load_district(request):
    country_id = request.GET.get('country_id')
    districts = district.objects.filter(state=country_id).all()
    return render(request, 'place_dropdown_list_options.html', {'districts': districts})





@login_required(login_url='ageis_app:adminlogin')
def jobs(request):
    try:
        if request.method == 'POST':
            form = JobsAddForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                company = data.get('company_name')
                if company is not None:
                    job = form.save(commit=False)
                    job.added_by = request.user
                    job.company = company
                    job.save()
                    messages.success(request, 'Job added successfully.')
                    return redirect('ageis_app:jobs')
                else:
                    messages.error(request, 'Invalid company selected.')
            else:
                messages.error(request, 'Error in the form submission. Please check the form data.')
        else:
            form = JobsAddForm()

        user_type = request.user.extenedusermodel.user_type


        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)


        jobs = Jobs.objects.all()


        if user_type == 'staff':
            jobs = jobs.filter(
                added_by=request.user,
                created_at__gte=last_30_days
            )
        elif user_type == 'manager':
            jobs = jobs.filter(created_at__gte=last_30_days)
        elif user_type == 'owner':
            pass  

        client_id = request.GET.get('client')
        if client_id:
            jobs = jobs.filter(company_id=client_id)

        # Filter by is_active
        is_active_filter = request.GET.get('is_active')
        if is_active_filter == 'true':
            jobs = jobs.filter(is_active=True)
        elif is_active_filter == 'false':
            jobs = jobs.filter(is_active=False)

        staff_filter = request.GET.get('staff')
        if staff_filter:
            print("staff Filter called",staff_filter)
            jobs = jobs.filter(added_by__id=staff_filter)

        staff_list = ExtendedUserModel.objects.filter(user_type='staff')
        context = {
            'form': form,
            'jobs': jobs,
            'clients': Clients.objects.all(),
            'user_type':user_type,
            'staff_list':staff_list
        }
        print("jobs",jobs)
        return render(request, 'jobs.html', context)
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('ageis_app:jobs')

@login_required(login_url='ageis_app:login')
def jobs_edit(request, update_id):
    try:
        # Retrieve the job instance or return a 404 if not found
        update = get_object_or_404(Jobs, id=update_id)
        
        if request.method == 'POST':
            form = JobsAddForm(request.POST, request.FILES, instance=update)
            if form.is_valid():
                form.save()
                messages.success(request, 'Job updated successfully.')
                return redirect('ageis_app:jobs')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = JobsAddForm(instance=update)
        
        context = {
            'form': form
        }
        return render(request, 'jobs-edit.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:jobs')  # Redirect to a fallback page, such as the job list



@login_required(login_url='ageis_app:login')
def job_delete(request, delete_id):
    try:
        # Get the job object or return a 404 error if not found
        job = get_object_or_404(Jobs, id=delete_id)
        job.delete()
        messages.success(request, 'Job deleted successfully.')
    except Jobs.DoesNotExist:
        # This block should not be reached due to get_object_or_404, but it’s good practice to handle it
        messages.error(request, 'Job not found.')
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, 'An unexpected error occurred. Please try again later.')
    
    return redirect('ageis_app:jobs')


@login_required(login_url='ageis_app:login')
def place_management(request):
    try:
        country = Country.objects.all()
        state = State.objects.all()
        district_list = district.objects.all()  # Ensure correct query

        context = {
            'country': country,
            'state': state,
            'district_list': district_list
        }
        
        return render(request, 'place-management.html', context)
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while retrieving the place data. Please try again later.")
        return render(request, 'place-management.html', {
            'country': [],
            'state': [],
            'district_list': [],
            'error_message': str(e)  # Pass the error message to the template if needed
        })



@login_required(login_url='ageis_app:login')
def country_add(request):
    try:
        if request.method == 'POST':
            country_name = request.POST.get('country')
            
            if not country_name:
                messages.error(request, 'Country name cannot be empty.')
                return redirect('ageis_app:place_management')

            # Create and save the Country object
            Country.objects.create(name=country_name).save()
            messages.success(request, 'Country successfully added.')
        
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    return redirect('ageis_app:place_management')



@login_required(login_url='ageis_app:login')
def country_update(request, country_id):
    try:
        # Fetch the country object, handle if not found
        updte = Country.objects.filter(id=country_id).first()
        if not updte:
            messages.error(request, "Country not found.")
            return redirect('ageis_app:place_management')

        if request.method == 'POST':
            # Update the country name with the provided data
            name = request.POST.get('name')
            if not name:
                messages.error(request, "Name field is required.")
                return render(request, 'edit-country.html', {'updte': updte})

            updte.name = name
            updte.save()
            messages.success(request, 'Country updated successfully.')
            return redirect('ageis_app:place_management')

        # Render the form with current data if not a POST request
        return render(request, 'edit-country.html', {'updte': updte})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:place_management')


@login_required(login_url='ageis_app:login')
def country_delete(request, country_id):
    try:
        # Attempt to get the country object or return a 404 if not found
        country = get_object_or_404(Country, id=country_id)
        
        # Delete the country object
        country.delete()
        
        # Show a success message
        messages.success(request, 'Country deleted successfully.')
        
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred while deleting the country: {e}")
        
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while trying to delete the country. Please try again later.")
    
    # Redirect to the place management page
    return redirect('ageis_app:place_management')


@login_required(login_url='ageis_app:login')
def state_add(request):
    try:
        if request.method == 'POST':
            country_name = request.POST.get('country')
            state_name = request.POST.get('state')

            if not country_name or not state_name:
                messages.error(request, 'Both country and state names are required.')
                return redirect('ageis_app:place_management')

            try:
                country = Country.objects.get(name=country_name)
            except Country.DoesNotExist:
                messages.error(request, f'Country "{country_name}" does not exist.')
                return redirect('ageis_app:place_management')

            # Create and save the new state
            State.objects.create(country=country, name=state_name)
            messages.success(request, 'Successfully added the state.')
        else:
            messages.error(request, 'Invalid request method.')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    return redirect('ageis_app:place_management')



@login_required(login_url='ageis_app:login')
def state_update(request, state_id):
    try:
        # Fetch all countries for the form
        country_list = Country.objects.all()
        
        # Fetch the state to be updated, or return a 404 if not found
        state_to_update = get_object_or_404(State, id=state_id)

        if request.method == 'POST':
            country_name = request.POST.get('country')
            try:
                # Try to fetch the country by name
                country = Country.objects.get(name=country_name)
            except Country.DoesNotExist:
                messages.error(request, f"Country '{country_name}' does not exist.")
                return render(request, 'edit-state.html', {'updte': state_to_update, 'country': country_list})
            
            # Update the state
            state_to_update.name = request.POST.get('name')
            state_to_update.country = country
            state_to_update.save()

            messages.success(request, 'State updated successfully.')
            return redirect('ageis_app:place_management')

        return render(request, 'edit-state.html', {'updte': state_to_update, 'country': country_list})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'edit-state.html', {'updte': state_to_update, 'country': country_list, 'error_message': str(e)})



@login_required(login_url='ageis_app:login')
def state_delete(request, state_id):
    try:
        # Try to get the State object or raise a 404 error if not found
        state = get_object_or_404(State, id=state_id)
        
        # Attempt to delete the State object
        state.delete()
        
        # Add a success message
        messages.success(request, 'State deleted successfully.')
    except State.DoesNotExist:
        # Handle the case where the state does not exist
        messages.error(request, 'State not found.')
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message for unexpected errors
        messages.error(request, "An unexpected error occurred while deleting the state. Please try again later.")
    
    # Redirect to the place management page
    return redirect('ageis_app:place_management')


@login_required(login_url='ageis_app:login')
def district_add(request):
    try:
        if request.method == 'POST':
            state_name = request.POST.get('state')
            district_name = request.POST.get('district')
            
            if not state_name or not district_name:
                messages.error(request, "State and District names are required.")
                return redirect('ageis_app:place_management')
            
            # Fetch the state object
            state = State.objects.filter(name=state_name).first()
            
            if not state:
                messages.error(request, f"State '{state_name}' not found.")
                return redirect('ageis_app:place_management')
            
            # Create the new district
            district.objects.create(state=state, name=district_name)
            messages.success(request, 'District successfully added.')

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    return redirect('ageis_app:place_management')



@login_required(login_url='ageis_app:login')
def district_update(request, district_id):
    try:
        # Fetch all states
        state_list = State.objects.all()

        # Fetch the district object, or return a 404 if not found
        dist = get_object_or_404(district, id=district_id)

        if request.method == 'POST':
            state_name = request.POST.get('country')
            state_obj = State.objects.filter(name=state_name).first()

            if state_obj is None:
                # If the state does not exist
                messages.error(request, 'The selected state does not exist.')
                return render(request, 'edit-state.html', {'updte': dist, 'country': state_list})

            # Update the district object with the new values
            dist.name = request.POST.get('name')
            dist.state = state_obj
            dist.save()
            messages.success(request, 'District updated successfully.')
            return redirect('ageis_app:place_management')

        return render(request, 'edit-state.html', {'updte': dist, 'country': state_list})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Display a generic error message
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return render(request, 'edit-state.html', {'updte': district, 'country': state_list, 'error_message': str(e)})




@login_required(login_url='ageis_app:login')
def district_delete(request, district_id):
    try:
        # Retrieve the district, or return a 404 error if not found
        district_obj = get_object_or_404(district, id=district_id)

        # Delete the district
        district_obj.delete()

        # Provide a success message
        messages.success(request, 'District deleted successfully.')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        
        # Provide an error message
        messages.error(request, 'An unexpected error occurred. Please try again later.')

    # Redirect to the place management page
    return redirect('ageis_app:place_management')

from django .core.paginator import Paginator, EmptyPage , PageNotAnInteger


def jobs_frontend(request):
    extended_user = None
    
    try:
        if request.user.is_authenticated:
            user = request.user
            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()

        all_jobs = Jobs.objects.all()
        per_page = 8
        paginator = Paginator(all_jobs, per_page)
        page = request.GET.get('page')

        try:
            jobs = paginator.page(page)
        except PageNotAnInteger:
            jobs = paginator.page(1)
        except EmptyPage:
            jobs = paginator.page(paginator.num_pages)

        context = {
            'jobs': jobs,
            'extended_user': extended_user,
        }
        return render(request, 'jobsfrontend.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        # Render the same page with error message
        return render(request, 'jobsfrontend.html', {
            'jobs': [],  # Optionally, you can display an empty list or previous jobs if needed
            'extended_user': extended_user,
            'error_message': str(e)  # Optional: Include specific error message in the context
        })


def jobs_frontend_cat(request, cat_id=None):
    try:
        if cat_id:
            if request.user.is_authenticated:
                user = request.user
                extended_user_qs = ExtendedUserModel.objects.filter(user=user)
                if extended_user_qs.exists():
                    extended_user = extended_user_qs.first()
            try:
                cat_id = int(cat_id)
                jobs = Jobs.objects.filter(job_category__id=cat_id)
            except ValueError:
                messages.error(request, "Invalid category ID.")
                return redirect('ageis_app:error_page')  # Redirect to a custom error page or home page
        else:
            jobs = Jobs.objects.all()

        context = {
            'jobs': jobs,
            'extended_user' : extended_user
        }
        return render(request, 'jobsfrontend.html', context)

    except Jobs.DoesNotExist:
        # Handle the case where the jobs query returns no results
        messages.error(request, "No jobs found for the selected category.")
        return render(request, 'jobsfrontend.html', {'jobs': []})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'jobsfrontend.html', {'jobs': []})
    
    
@login_required(login_url='ageis_app:login')
def jobs_details(request, job_id):
    job = None
    extenedusermodel = None
    applied = False
    error_message = None

    try:
        # Fetch the job details or return a 404 error if not found
        job = get_object_or_404(Jobs, id=job_id)

        # Ensure that the user has an associated ExtendedUserModel
        if not hasattr(request.user, 'extenedusermodel'):
            error_message = "Your profile is incomplete. Please complete your profile to apply for jobs."
            extenedusermodel = None
        else:
            extenedusermodel = request.user.extenedusermodel

            # Check if the job has already been applied by the user
            applied = AppliedJobs.objects.filter(applied_user=extenedusermodel, applied_job=job).exists()

    except Jobs.DoesNotExist:
        error_message = "The job you are looking for does not exist."
        # You can redirect to a different page if needed
        return render(request, 'error.html', {'error_message': error_message})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        error_message = "An unexpected error occurred. Please try again later."
        # You can redirect to a different page if needed
        return render(request, 'error.html', {'error_message': error_message})

    # Render the job details page with context
    return render(request, 'job-details.html', {
        'details': job,
        'applied': applied,
        'extenedusermodel': extenedusermodel,
        'error_message': error_message,
    })




@login_required(login_url='ageis_app:adminlogin')
def user_management(request):
    try:
        user_type = request.user.extenedusermodel.user_type
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        # Check if a specific user ID is provided
        user_id_filter = request.GET.get('user_id')

        if user_id_filter:
            if user_type == 'staff':
                userlist = ExtendedUserModel.objects.filter(id=user_id_filter,created_by=request.user,user_type='user')
            elif user_type =='manager' or user_type == 'owner':
                userlist = ExtendedUserModel.objects.filter(id=user_id_filter,user_type='user')
        else:
            userlist = ExtendedUserModel.objects.filter(
                user__is_staff=False,
                user__is_superuser=False
            ).order_by('-id').select_related('user').prefetch_related('user__preferred_job_titles', 'user__languages')

            if user_type == 'staff':
                userlist = userlist.filter(
                    created_by=request.user,
                    created_at__gte=last_30_days,
                    user_type='user'
                )
            elif user_type == 'manager':
                userlist = userlist.filter(created_at__gte=last_30_days,user_type='user')

            # Apply other filters
            skill_filter = request.GET.get('skill')
            qualification_filter = request.GET.get('qualification')
            experience_filter = request.GET.get('experience')
            country_filter = request.GET.get('country')
            state_filter = request.GET.get('state')
            district_filter = request.GET.get('district')
            location_filter = request.GET.get('location')
            relocate_filter = request.GET.get('relocate')
            job_title_filter = request.GET.get('job_title')
            languages_filter = request.GET.get('languages')
            active_candidates_filter = request.GET.get('active_candidates')
            staff_filter = request.GET.get('staff')

            if skill_filter:
                skills = [skill.strip() for skill in skill_filter.split(',')]
                for skill in skills:
                    user_ids_with_skill = Skills.objects.filter(skill__icontains=skill).values_list('user_id', flat=True)
                    userlist = userlist.filter(id__in=user_ids_with_skill)

            if qualification_filter:
                user_ids_with_qualification = Qualification.objects.filter(degree__icontains=qualification_filter).values_list('user_id', flat=True)
                userlist = userlist.filter(id__in=user_ids_with_qualification)

            if experience_filter:
                user_ids_with_experience = Experience.objects.filter(description__icontains=experience_filter).values_list('user_id', flat=True)
                userlist = userlist.filter(id__in=user_ids_with_experience)

            if country_filter:
                userlist = userlist.filter(country__iregex=country_filter)

            if state_filter:
                userlist = userlist.filter(state__iregex=state_filter)

            if district_filter:
                userlist = userlist.filter(district__iregex=district_filter)

            if location_filter:
                userlist = userlist.filter(location__iregex=location_filter)

            if relocate_filter:
                userlist = userlist.filter(relocate=True)
                
            if active_candidates_filter:
                userlist = userlist.filter(user__is_active=True)

            if job_title_filter:
                job_titles = [title.strip() for title in job_title_filter.split(',')]
                for title in job_titles:
                    user_ids_with_job_title = PreferredJobTitle.objects.filter(job_title__icontains=title).values_list('user_id', flat=True)
                    userlist = userlist.filter(user_id__in=user_ids_with_job_title)

            if languages_filter:
                languages = [language.strip() for language in languages_filter.split(',')]
                for language in languages:
                    user_ids_with_language = Language.objects.filter(language__icontains=language).values_list('user_id', flat=True)
                    userlist = userlist.filter(user_id__in=user_ids_with_language)

            if staff_filter:
                userlist = userlist.filter(created_by__id=staff_filter)

        staff_list = ExtendedUserModel.objects.filter(user_type='staff')

        return render(request, 'user-management.html', {
            'userlist': userlist,
            'staff_list': staff_list,
            'user_type': user_type
        })
    
    except PermissionDenied as e:
        messages.error(request, str(e))
        return render(request, 'user-management.html', {
            'userlist': [],
            'staff_list': ExtendedUserModel.objects.filter(user_type='staff'),
            'user_type': request.user.extenedusermodel.user_type,
            'error_message': str(e)
        })
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        messages.error(request, "An unexpected error occurred while processing your request. Please try again later.")
        return render(request, 'user-management.html', {
            'userlist': [],
            'staff_list': ExtendedUserModel.objects.filter(user_type='staff'),
            'user_type': request.user.extenedusermodel.user_type,
            'error_message': str(e)
        })
    
from django.db import DatabaseError
@login_required(login_url='ageis_app:login')
def apply_job(request, job_id):
    first_name = request.user.first_name
    last_name = request.user.last_name
    full_name = f'{first_name} {last_name}'

    try:
        # Fetch the job object
        jobs = Jobs.objects.get(id=job_id)
    except Jobs.DoesNotExist:
        messages.error(request, 'Job not found.')
        return redirect('ageis_app:jobs_frontend')

    try:
        # Fetch the extended user profile
        user = ExtendedUserModel.objects.get(user=request.user)
    except ExtendedUserModel.DoesNotExist:
        messages.error(request, 'User profile not found. Please complete your profile.')
        return redirect('ageis_app:user_profile')

    # Check for missing fields
    missing_fields = []
    if not first_name or not last_name:
        missing_fields.append('full name')
    if not user.phone:
        missing_fields.append('phone number')
    if not user.cv:
        missing_fields.append('CV')
    if not user.gender:
        missing_fields.append('gender')
    if not user.location:
        missing_fields.append('location')

    if missing_fields:
        missing_fields_message = ', '.join(missing_fields)
        messages.error(request, f'Please complete the following fields in your profile: {missing_fields_message}.')
        return redirect('ageis_app:user_profile')

    try:
        # Increment the application count
        if jobs.application_count is None:
            jobs.application_count = 0
        jobs.application_count = F('application_count') + 1
        jobs.save()
        jobs.refresh_from_db()

        # Create an applied job entry
        AppliedJobs.objects.create(
            applied_user=user,
            applied_job=jobs
        )
        messages.success(request, 'Job applied successfully.')

    except DatabaseError as e:
        # Handle database errors
        print(f"Database error occurred: {e}")
        messages.error(request, "An error occurred while applying for the job. Please try again later.")

    except Exception as e:
        # Handle other unexpected errors
        print(f"An unexpected error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    return redirect('ageis_app:jobs_frontend')


def applied_jobs(request):
    try:
        user_type = request.user.extenedusermodel.user_type
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        app_id = request.GET.get('app_id')

        applied_jobs = AppliedJobs.objects.all()
        clients = Clients.objects.all()
        jobs = Jobs.objects.all()

        if app_id:
            if user_type == 'staff':
                applied_jobs = AppliedJobs.objects.filter(id=app_id, applied_job__created_by=request.user)
            else:
                applied_jobs = AppliedJobs.objects.filter(id=app_id)

        else:
            # Apply the rest of the filters only if app_id is not present
            # Filtering by clients
            client_id = request.GET.get('client')
            if client_id:
                applied_jobs = applied_jobs.filter(applied_job__company_id=client_id)

            # Filtering by Jobs
            job_id = request.GET.get('job')
            if job_id:
                applied_jobs = applied_jobs.filter(applied_job_id=job_id)

            # Filtering by relocation capability
            relocate_filter = request.GET.get('relocate')
            if relocate_filter:
                applied_jobs = applied_jobs.filter(applied_user__relocate=True)

            # Filtering by candidate location
            country = request.GET.get('country')
            state = request.GET.get('state')
            district = request.GET.get('district')
            location = request.GET.get('location')

            if country:
                applied_jobs = applied_jobs.filter(applied_user__country__icontains=country)
            if state:
                applied_jobs = applied_jobs.filter(applied_user__state__icontains=state)
            if district:
                applied_jobs = applied_jobs.filter(applied_user__district__icontains=district)
            if location:
                applied_jobs = applied_jobs.filter(applied_user__location__icontains=location)

            # Additional filters based on user type
            if user_type == 'staff':
                user_jobs = Jobs.objects.filter(added_by=request.user)
                applied_jobs = applied_jobs.filter(
                    applied_job__in=user_jobs,
                    applied_date__gte=last_30_days
                )
            elif user_type == 'manager':
                applied_jobs = applied_jobs.filter(applied_date__gte=last_30_days)

            # Filtering by staff
            staff_filter = request.GET.get('staff')
            if staff_filter:
                applied_jobs = applied_jobs.filter(applied_job__added_by=staff_filter)

        staff_list = ExtendedUserModel.objects.filter(user_type='staff')

        return render(request, 'applied-jobs-lists.html', {
            'applied_jobs': applied_jobs,
            'clients': clients,
            'jobs': jobs,
            'user_type': user_type,
            'staff_list': staff_list
        })

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while retrieving applied jobs. Please try again later.")
        # Redirect to the error page or render an error template
        return render(request, 'applied-jobs-lists.html', {
            'applied_jobs': [],
            'clients': clients,
            'jobs': jobs,
            'user_type': user_type,
            'staff_list': []
        })
            


def search_jobs(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()
        query = request.GET.get('query', '')

        # Ensure query is a string and handle potential invalid queries
        if not isinstance(query, str):
            raise ValueError("Invalid query parameter")

        # Perform the search
        jobs = Jobs.objects.filter(job_title__icontains=query)
        
        # Prepare the jobs list for the response
        jobs_list = [
            {
                'id': job.id,
                'job_title': job.job_title,
                'company_name': job.company.company_name
            } for job in jobs
        ]
        
        return JsonResponse({'jobs': jobs_list ,'extended_user' : extended_user})

    except ValueError as ve:
        # Handle invalid query parameter
        return JsonResponse({'error': str(ve)}, status=400)
    
    except ObjectDoesNotExist:
        # Handle case where no jobs are found (this is optional)
        return JsonResponse({'error': 'No jobs found'}, status=404)
    
    except Exception as e:
        # Handle any other unexpected errors
        return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)


def shortlist_candidate(request, job_id):
    try:
        # Get the applied job object
        applied_job = get_object_or_404(AppliedJobs, id=job_id)
        
        # Update the applied job status
        applied_job.is_shortlisted = True
        applied_job.save()
        
        # Retrieve the candidate's email address
        candidate_email = applied_job.applied_user.user.email
        
        # Retrieve job details
        job = applied_job.applied_job
        job_title = job.job_title
        job_company = job.company.company_name  # Assuming 'company_name' is the attribute for the company name
        job_description = job.job_des

        # Compose the email
        email_subject = 'Congratulations! You have been shortlisted for a job'
        email_body = (
            f'Dear candidate,\n\n'
            f'We are pleased to inform you that you have been shortlisted for the following job:\n\n'
            f'Job Title: {job_title}\n'
            f'Company: {job_company}\n'
            f'Description: {job_description}\n\n'
            f'Please contact us for further instructions.\n\n'
            f'Best regards,\n'
            f'The Recruitment Team'
        )

        # Send the email
        send_mail(
            email_subject,
            email_body,
            settings.EMAIL_HOST_USER,  # Sender's email address
            [candidate_email],  # Recipient's email address
            fail_silently=False,
        )

        # Success message
        messages.success(request, 'Candidate has been shortlisted and notified via email.')

    except DatabaseError as e:
        # Handle database errors
        print(f"Database error occurred: {e}")
        messages.error(request, "An error occurred while updating the candidate's status. Please try again later.")
    
    except Exception as e:
        # Handle general errors
        print(f"An unexpected error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    return redirect('ageis_app:applied_jobs')


def schedule_interview(request):
    if request.method == 'POST':
        applied_job_id = request.POST.get('applied_job_id')
        applied_job = AppliedJobs.objects.get(pk=applied_job_id)
        candidate_email = applied_job.applied_user.user.email
        job = applied_job.applied_job

        # Retrieve the subject from the form
        subject = request.POST.get('subject')
        date = request.POST.get('date')
        time = request.POST.get('time')
        if not subject:
            subject = 'Interview Invitation'

        # Compose the email
        email_body = (
            f'Dear candidate,\n\n'
            f'We are pleased to invite you for an interview for the position of {job.job_title} '
            f'at {job.company.company_name}.\n\n'
            f'Your application stood out to us, and we would like to learn more about your qualifications.\n'
            f'Please find the details below:\n\n'
            f'Date: {date}\n'
            f'Time: {time}\n'
           f'\n\n{subject}\n\n'
            f'\n\nWe look forward to meeting you and discussing your potential role at {job.company.company_name}\n\n'
            f'Best regards,\n'
            f'The Recruitment Team'
        )

        # Send the email
        send_mail(
            subject,
            email_body,
            settings.EMAIL_HOST_USER,  # Sender's email address
            [candidate_email],  # Recipient's email address
            fail_silently=False,
        )

        # Update the is_invited field
        applied_job.is_invited = True
        applied_job.save()

        return redirect('ageis_app:shortlisted_jobs')
    else:
        # Handle GET request
        return redirect('ageis_app:shortlisted_jobs')
    

from django.core.mail import EmailMessage
import logging

logger = logging.getLogger(__name__)

def send_offer_letter(request):
    if request.method == 'POST':
        logger.debug("Offer letter sent POST")
        applied_job_id = request.POST.get('applied_job_id')
        logger.debug(f'Received applied_job_id: {applied_job_id}')

        if not applied_job_id:
            logger.error('Applied job ID is empty')
            return JsonResponse({'success': False, 'error': 'Applied job ID is empty'})

        try:
            applied_job_id = int(applied_job_id)
            applied_job = AppliedJobs.objects.get(pk=applied_job_id)
        except ValueError:
            logger.error(f'Invalid job ID: {applied_job_id}')
            return JsonResponse({'success': False, 'error': 'Invalid job ID'})
        except AppliedJobs.DoesNotExist:
            logger.error(f'Applied job does not exist: {applied_job_id}')
            return JsonResponse({'success': False, 'error': 'Applied job does not exist'})

        candidate_email = applied_job.applied_user.user.email
        logger.debug(f'Candidate email: {candidate_email}')

        offer_letter_file = request.FILES.get('offer_letter_file')
        email_subject = request.POST.get('email_subject')
        email_body = request.POST.get('email_body')

        if offer_letter_file:
            # Verify the file is not empty
            if offer_letter_file.size > 0:
                logger.debug(f'File received: {offer_letter_file.name}, Type: {offer_letter_file.content_type}, Size: {offer_letter_file.size} bytes')
                applied_job.offer_letter = offer_letter_file
                applied_job.save()

                # Create email with attachment
                email = EmailMessage(
                    email_subject,
                    email_body,
                    settings.EMAIL_HOST_USER,
                    [candidate_email],
                    reply_to=[settings.EMAIL_HOST_USER]
                )
                email.attach(
                    offer_letter_file.name,
                    offer_letter_file.read(),
                    offer_letter_file.content_type
                )
            else:
                print("Received file is empty")
                logger.error('Received file is empty')
                return JsonResponse({'success': False, 'error': 'Received file is empty'})
        else:
            email = EmailMessage(
                email_subject,
                email_body,
                settings.EMAIL_HOST_USER,
                [candidate_email],
                reply_to=[settings.EMAIL_HOST_USER]
            )

        try:
            email.send(fail_silently=False)
        except Exception as e:
            logger.error(f'Error sending email: {e}')
            return JsonResponse({'success': False, 'error': str(e)})

        applied_job.result = 'offerletter_sent' 
        applied_job.save()
        return JsonResponse({'success': True})

    logger.error('Invalid request method')
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


from django.http import JsonResponse
def update_interview_result(request, job_id):
    applied_job = AppliedJobs.objects.get(pk=job_id)
    result = request.POST.get('result')  # Assuming 'result' is passed in the AJAX request
    if result == 'selected':
        applied_job.result = 'selected'
    elif result == 'rejected':
        applied_job.result = 'rejected'
    elif result == 'on_hold':
        applied_job.result = 'on_hold'
    applied_job.save()
    return JsonResponse({'status': 'success'})


def shortlisted_jobs(request):
    clients = []
    jobs = []
    applied_jobs = []
    selected_client_id = None
    selected_job_id = None

    try:
        user_is_staff = request.user.extenedusermodel.user_type == 'staff'
        clients = Clients.objects.all()
        jobs = Jobs.objects.all()

        # If a client is selected from the dropdown
        selected_client_id = request.GET.get('client')
        if selected_client_id:
            selected_client_id = int(selected_client_id)  # Convert to integer for filtering
            selected_client = get_object_or_404(Clients, pk=selected_client_id)
            jobs = jobs.filter(company=selected_client)
            applied_jobs = AppliedJobs.objects.filter(
                applied_job__company=selected_client,
                is_shortlisted=True
            )
        else:
            applied_jobs = AppliedJobs.objects.filter(is_shortlisted=True)

        # If a job is selected from the dropdown
        selected_job_id = request.GET.get('job')
        if selected_job_id:
            selected_job_id = int(selected_job_id)  # Convert to integer for filtering
            selected_job = get_object_or_404(Jobs, pk=selected_job_id)
            applied_jobs = applied_jobs.filter(applied_job=selected_job)


        if user_is_staff:
            applied_jobs = applied_jobs.filter(applied_job__added_by=request.user)


    except ValueError as e:
        # Handle invalid integer conversion for client or job IDs
        messages.error(request, "Invalid input provided. Please select valid options.")
        print(f"ValueError: {e}")
        return render(request, 'shortlisted_jobs.html', {
            'clients': clients,
            'jobs': jobs,
            'applied_jobs': applied_jobs,
            'selected_client_id': selected_client_id,
            'selected_job_id': selected_job_id,
        })

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'shortlisted_jobs.html', {
            'clients': clients,
            'jobs': jobs,
            'applied_jobs': applied_jobs,
            'selected_client_id': selected_client_id,
            'selected_job_id': selected_job_id,
        })

    return render(request, 'shortlisted_jobs.html', {
        'clients': clients,
        'jobs': jobs,
        'applied_jobs': applied_jobs,
        'selected_client_id': selected_client_id,
        'selected_job_id': selected_job_id,
    })



from django.http import Http404
def remove_from_shortlist(request, job_id):
    try:
        # Try to get the AppliedJobs object or raise 404 if not found
        applied_job = get_object_or_404(AppliedJobs, id=job_id)

        # Update the `is_shortlisted` field
        applied_job.is_shortlisted = False
        applied_job.save()

        # Display a success message
        messages.success(request, 'Job removed from shortlist successfully.')

    except Http404:
        # Handle the case where the job is not found
        messages.error(request, 'Job not found.')
    
    except Exception as e:
        # Handle any other exceptions
        print(f"An error occurred: {e}")
        messages.error(request, 'An unexpected error occurred. Please try again later.')

    # Redirect to the applied jobs page
    return redirect('ageis_app:applied_jobs')


def filter_results(request):
    try:
        selected_result = request.GET.get('result')

        if selected_result:
            # Validate the selected_result to be one of the acceptable values
            if selected_result in ['placed', 'on_hold', 'rejected']:
                applied_jobs = AppliedJobs.objects.filter(result=selected_result)
            else:
                # If the selected_result is not valid, handle the case
                messages.warning(request, "Invalid filter option selected. Showing all results.")
                applied_jobs = AppliedJobs.objects.filter(result__in=['placed', 'on_hold', 'rejected'])
        else:
            # Default case when no filter is applied
            applied_jobs = AppliedJobs.objects.filter(result__in=['placed', 'on_hold', 'rejected'])

        return render(request, 'filtered_results.html', {'applied_jobs': applied_jobs})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed in the template
        messages.error(request, "An unexpected error occurred while filtering results. Please try again later.")
        # Render the page with no results or a suitable message
        return render(request, 'filtered_results.html', {'applied_jobs': []})


def applied_jobs_delete(request, job_id):
    try:
        # Attempt to get the job entry to delete
        job = AppliedJobs.objects.get(id=job_id)
        job.delete()
        messages.success(request, 'Applied job successfully deleted.')
    except AppliedJobs.DoesNotExist:
        # Handle the case where the job does not exist
        messages.error(request, 'The job you are trying to delete does not exist.')
    except Exception as e:
        # Handle other possible exceptions
        print(f"An error occurred: {e}")
        messages.error(request, 'An unexpected error occurred. Please try again later.')

    return redirect('ageis_app:applied_jobs')



def blogs(request):
    try:
        # Fetch all testimonials
        testimonials = Testimonials.objects.all()
        
        # Render the template with testimonials
        return render(request, 'blog.html', {'testimonials': testimonials})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while fetching blogs. Please try again later.")
        # Redirect to a custom error page or render the same template with an error message
        return render(request, 'blog.html', {'testimonials': [], 'error_message': str(e)})


def about_us(request):
    try:
        extended_user = None  
        if request.user.is_authenticated:
            user = request.user
            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()

        job_posted_count = Jobs.objects.count()
        applied_jobs_count = AppliedJobs.objects.count()
        company_count = Clients.objects.count()
        members_count = ExtendedUserModel.objects.count()
        about_us = AboutUs.objects.all()

        context = {
            'job_posted_count': job_posted_count,
            'applied_jobs_count': applied_jobs_count,
            'company_count': company_count,
            'members_count': members_count,
            'about_us': about_us,
            'extended_user': extended_user,
        }

        return render(request, 'about.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        # Render the template with an error message in the context
        return render(request, 'about.html', {
            'job_posted_count': 0,
            'applied_jobs_count': 0,
            'company_count': 0,
            'members_count': 0,
            'about_us': [],
            'extended_user': extended_user,
            'error_message': str(e),
        })


@login_required(login_url='ageis_app:login')
def about_us_backend(request):
    form = AboutUsAddForm()  # Initialize the form before the try block to handle both cases

    try:
        if request.method == 'POST':
            form = AboutUsAddForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Information added successfully.')
                return redirect('ageis_app:about_us_backend')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        
        about_us = AboutUs.objects.all()
        context = {
            'form': form,
            'about_us': about_us
        }
        return render(request, 'about-us-backend.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        about_us = AboutUs.objects.all()  # Ensure we still fetch existing AboutUs objects even in case of an error
        return render(request, 'about-us-backend.html', {
            'form': form,
            'about_us': about_us,
            'error_message': str(e)
        })




@login_required(login_url='ageis_app:login')
def aboutus_edit(request, update_id):
    try:
        # Retrieve the AboutUs object or return 404 if not found
        update = get_object_or_404(AboutUs, id=update_id)
        
        if request.method == 'POST':
            form = AboutUsAddForm(request.POST, instance=update)
            if form.is_valid():
                form.save()
                messages.success(request, 'Updated successfully.')
                return redirect('ageis_app:about_us_backend')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = AboutUsAddForm(instance=update)
        
        context = {
            'form': form
        }
        return render(request, 'about-us-edit.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        # Render the form with an error message in case of an unexpected error
        return render(request, 'about-us-edit.html', {'form': form, 'error_message': str(e)})





def aboutus_delete(request, about_id):
    try:
        # Try to get the AboutUs instance
        about = get_object_or_404(AboutUs, id=about_id)
        
        # Delete the instance
        about.delete()
        
        # Show success message
        messages.success(request, 'Deleted successfully.')
        return redirect('ageis_app:about_us_backend')
    
    except AboutUs.DoesNotExist:
        # Handle the case where the object does not exist
        messages.error(request, 'The item you are trying to delete does not exist.')
        return redirect('ageis_app:about_us_backend')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:about_us_backend')






def clients(request):
    try:
        extended_user = None

        if request.user.is_authenticated:
            user = request.user
            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()

        companies = Clients.objects.all()

        context = {
            'companies': companies,
            'extended_user': extended_user
        }
        return render(request, 'clients-frontend.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        # Render the template with an error message
        return render(request, 'clients-frontend.html', {'error_message': str(e)})




def resume_writing(request):
    extended_user = None
    try:
        if request.user.is_authenticated:
            user = request.user
            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()
        
        context = {
            'extended_user': extended_user
        }
        return render(request, 'resumewriting.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while retrieving your profile. Please try again later.")
        return render(request, 'resumewriting.html', {'error_message': "An unexpected error occurred while retrieving your profile. Please try again later."})



def interviewtips(request):
    try:
        extended_user = None
        if request.user.is_authenticated:
            user = request.user
            extended_user_qs = ExtendedUserModel.objects.filter(user=user)
            if extended_user_qs.exists():
                extended_user = extended_user_qs.first()

        context = {
            'extended_user': extended_user
        }
        return render(request, 'interviewtips.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed
        messages.error(request, "An unexpected error occurred while retrieving interview tips. Please try again later.")
        return render(request, 'interviewtips.html', {'extended_user': None})



def contact_us(request):
    extended_user = None
    if request.user.is_authenticated:
        user = request.user
        extended_user_qs = ExtendedUserModel.objects.filter(user=user)
        if extended_user_qs.exists():
            extended_user = extended_user_qs.first()

    context = {
        'extended_user': extended_user
    }

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email1 = request.POST.get('email')
            number = request.POST.get('number')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            # Basic validation to ensure all fields are provided
            if not all([name, email1, number, subject, message]):
                messages.error(request, 'All fields are required. Please fill in all fields.')
                return render(request, 'contact-us.html', context)
            
            email_body = (
                f'Name: {name}\n'
                f'Email: {email1}\n'
                f'Phone: {number}\n'
                f'Subject: {subject}\n'
                f'Message: {message}'
            )
            
            send_mail(
                'Enquiry',
                email_body,
                settings.EMAIL_HOST_USER,
                ['support@ageisrecruitment.online'],
                fail_silently=False,
            )
            
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('ageis_app:contact_us')

        except Exception as e:
            # Log the exception or handle it as needed
            print(f"An error occurred: {e}")
            messages.error(request, "An unexpected error occurred while sending your message. Please try again later.")
            return render(request, 'contact-us.html', context)
    
    return render(request, 'contact-us.html', context)
# def contact_us(request):
#     if request.method == 'POST':
#         print(request.POST)
#         form = ContactForm(request.POST)
#         form.save()
#         email = "achujoseph@a2zalphabetsolutionz.com"  # Use the correct sender email address

#         send_mail(
#             'Enquiry',
#             f'Name: {form.cleaned_data["name"]}\nEmail: {form.cleaned_data["email"]}\nMessage: {form.cleaned_data["message"]}',
#             (email),
#             [settings.EMAIL_HOST_USER],
#             fail_silently=False,    
#         )
#         print('Form submited..')
#         return render(request,'thank_you.html')
#     else:
#         form = ContactForm()
#     return render(request,'index.html', {'form': form})

def job_search(request):
    try:
        # Use GET to retrieve the 'title' from the query parameters
        job_title = request.GET.get('title')
        user = request.user

        query = Q()

        # Only add the job_title filter if job_title is not None
        if job_title:
            query &= Q(job_title__icontains=job_title)

        results = Jobs.objects.filter(query)

        # Save the first result of the search to RecentlySearchedJobs, if any
        job = results.first()
        if job and user.is_authenticated and not RecentlySearchedJobs.objects.filter(user=user, job=job).exists():
            RecentlySearchedJobs.objects.create(user=user, job=job)

        context = {
            'jobs': results
        }
        return render(request, 'jobsfrontend.html', context)

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred during job search: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred while searching for jobs. Please try again later.")
        # Redirect to a generic search results page or the same search page
        return render(request, 'jobsfrontend.html', {'jobs': []})

def render_template(request, template_name):
    return render(request, template_name)

def render_disclaimer(request):
    return render(request, 'disclaimer.html')

def render_terms(request):
    return render(request, 'terms.html')

def render_faq(request):
    return render(request, 'faq.html')

def render_privacy(request):
    return render(request, 'privacy.html')


@login_required(login_url='ageis_app:login')
def user_profile(request):
    print("Called user_profile")
    try:
        print("Called user_profile TRY")
        user = request.user.extenedusermodel
        skills = user.skills.all()
        qualifications = user.qualifications.all()
        experiences = user.experiences.all()
        applied_jobs = AppliedJobs.objects.filter(applied_user=user)
        languages = user.user.languages.all()
        preferred_job_titles = user.user.preferred_job_titles.all()

        context = {
            'user': user,
            'skills': skills,
            'qualifications': qualifications,
            'experiences': experiences,
            'applied_jobs': applied_jobs,
            'languages': languages,
            'preferred_job_titles': preferred_job_titles,
        }
        return render(request, 'user_profile.html', context)
    
    except ExtendedUserModel.DoesNotExist:
        # Handle case where the ExtendedUserModel instance does not exist
        messages.error(request, 'User profile does not exist.')
        return render(request, 'error.html', {'message': 'User profile does not exist.'})
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return render(request, 'error.html', {'message': str(e)})
    


@login_required
def add_job_title(request):
    try:
        if request.method == 'POST':
            job_titles = request.POST.get('job_title')
            
            if job_titles:
                # Split the input string by commas and strip any whitespace
                job_title_list = [title.strip() for title in job_titles.split(',')]
                
                # Create a PreferredJobTitle object for each title in the list
                for title in job_title_list:
                    if title:  # Ensure no empty strings are processed
                        PreferredJobTitle.objects.create(user=request.user, job_title=title)
                
                messages.success(request, 'Job titles added successfully.')
            else:
                messages.warning(request, 'No job titles provided.')
        
        return redirect('ageis_app:user_profile')

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the user profile page
        messages.error(request, "An unexpected error occurred while adding job titles. Please try again later.")
        return redirect('ageis_app:user_profile')
    

@login_required
def delete_job_title(request, job_title_id):

    user_type = request.user.extenedusermodel.user_type 

    try:
        if user_type == 'user':
            job_title = get_object_or_404(PreferredJobTitle, id=job_title_id, user=request.user)
            if job_title.user != request.user:
                return HttpResponseForbidden("You do not have permission to delete this job title.")

            job_title.delete()
            messages.success(request, 'Job title deleted successfully.')
            
        else:
            job_title = get_object_or_404(PreferredJobTitle, id=job_title_id)
            job_title.delete()
            return JsonResponse({'status': 'success', 'message': 'Job title deleted successfully.'})
        
    except Exception as e:
        print(f"An error occurred: {e}")

        if user_type == 'user':
            messages.error(request, 'An unexpected error occurred while deleting the job title. Please try again later.')
        else:
            return JsonResponse({'status': 'error', 'message': 'An error occurred while deleting the job title. Please try again.'}, status=500)
    return redirect('ageis_app:user_profile')




def delete_skill(request, skill_id):
    try:
        # Retrieve the skill object or return a 404 error if not found
        skill = get_object_or_404(Skills, id=skill_id)
        
        # Attempt to delete the skill
        skill.delete()
        
        # Provide a success message
        messages.success(request, 'Skill deleted successfully.')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred while deleting the skill: {e}")
        
        # Add an error message to be displayed
        messages.error(request, "An unexpected error occurred. The skill could not be deleted. Please try again later.")
    
    # Redirect to the user profile page
    return redirect('ageis_app:user_profile')


@login_required(login_url='ageis_app:login')
def add_qualification(request):
    try:
        if request.method == 'POST':
            form = QualificationForm(request.POST)
            if form.is_valid():
                qualification = form.save(commit=False)
                qualification.user = request.user.extenedusermodel
                qualification.save()
                messages.success(request, 'Qualification added successfully.')
                return redirect('ageis_app:user_profile')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = QualificationForm()
        
        return render(request, 'add_qualification.html', {'form': form})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed in the template
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'add_qualification.html', {'form': form, 'error_message': str(e)})
    
@login_required(login_url='ageis_app:login')
def delete_qualification(request, qualification_id):
    try:
        # Retrieve the Qualification object or return a 404 error if not found
        qualification = get_object_or_404(Qualification, id=qualification_id)
        
        # Delete the Qualification object
        qualification.delete()
        
        # Show a success message to the user
        messages.success(request, 'Qualification deleted successfully.')
        
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred while deleting the qualification: {e}")
        
        # Show an error message to the user
        messages.error(request, "An unexpected error occurred while deleting the qualification. Please try again later.")
        
        # Redirect to an error page or render a template if needed
        return HttpResponseServerError("An unexpected error occurred. Please try again later.")
    
    # Redirect the user back to the profile page
    return redirect('ageis_app:user_profile')

@login_required(login_url='ageis_app:login')
def add_experience(request):
    form = None
    try:
        if request.method == 'POST':
            form = ExperienceForm(request.POST)
            if form.is_valid():
                experience = form.save(commit=False)
                experience.user = request.user.extenedusermodel
                experience.save()
                messages.success(request, 'Experience added successfully.')
                return redirect('ageis_app:user_profile')
            else:
                # Handle form validation errors
                messages.error(request, 'Please correct the errors below.')
        else:
            form = ExperienceForm()
        
        # Render the profile page with the form in case of GET or validation errors
        return render(request, 'user_profile.html', {'form': form})

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the profile page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        # Render the profile page with the form and error message
        return render(request, 'user_profile.html', {'form': form, 'error_message': str(e)})




# def delete_experience(request, experience_id):
#     experience = get_object_or_404(Experience, id=experience_id)
#     experience.delete()
#     messages.success(request, 'Experience deleted successfully.')
#     return redirect('user_profile')
from django.core.files.uploadedfile import InMemoryUploadedFile

@login_required
def profile_update(request):
    try:
        # Retrieve the user's profile
        user_profile = ExtendedUserModel.objects.get(user=request.user)

        if request.method == 'POST':
            # Extract data from the POST request
            new_first_name = request.POST.get('firstname', '')
            new_last_name = request.POST.get('lastname', '')
            new_position = request.POST.get('position', '')
            current_company = request.POST.get('company', '')
            current_start_date = request.POST.get('current_start_date', None)
            description = request.POST.get('discription', '')
            currently_working = request.POST.get('currently_working') == 'on'  # Checkbox value
            location = request.POST.get('location', '')

            # Update the user details in the ExtendedUserModel instance
            user_profile.user.first_name = new_first_name
            user_profile.user.last_name = new_last_name
            user_profile.position = new_position
            user_profile.current_company = current_company
            user_profile.current_start_date = current_start_date if current_start_date else None
            user_profile.discription = description
            user_profile.currently_working = currently_working
            user_profile.location = location

            # Handle file upload for profile photo
            profile_photo = request.FILES.get('pic')
            if profile_photo:
                if isinstance(profile_photo, InMemoryUploadedFile):  # Check if it's a valid file
                    user_profile.profile_photo = profile_photo

            # Save the changes
            user_profile.user.save()
            user_profile.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('ageis_app:user_profile')
        else:
            form = ExtendedUserModelForm(instance=user_profile)

        return render(request, 'user_profile.html', {'form': form})

    except ObjectDoesNotExist:
        messages.error(request, 'User profile does not exist.')
        return redirect('ageis_app:error_page')  # Redirect to a custom error page

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'user_profile.html', {'form': form, 'error_message': str(e)})
    
    
@login_required
def contact_update(request):
    try:
        # Fetch the user's profile
        user_profile = ExtendedUserModel.objects.get(user=request.user)

        if request.method == 'POST':
            # Extract data from the POST request
            new_phone = request.POST.get('number', '')
            new_email = request.POST.get('email', '')
            new_district = request.POST.get('district', '')
            new_state = request.POST.get('state', '')
            new_country = request.POST.get('country', '')
            new_address = request.POST.get('address', '')
            new_dob = request.POST.get('dob', '')
            new_gender = request.POST.get('gender', '')
            new_relocate = request.POST.get('relocate') == 'on'

            # Update the user details in the ExtendedUserModel instance
            user_profile.user.email = new_email
            user_profile.phone = new_phone
            user_profile.district = new_district
            user_profile.state = new_state
            user_profile.country = new_country
            user_profile.address = new_address
            user_profile.dob = new_dob
            user_profile.gender = new_gender
            user_profile.relocate = new_relocate

            # Save the changes
            user_profile.user.save()
            user_profile.save()

            return redirect('ageis_app:user_profile')
        else:
            form = ExtendedUserModelForm(instance=user_profile)

        return render(request, 'user_profile.html', {'form': form})

    except ObjectDoesNotExist:
        messages.error(request, "User profile does not exist.")
        return redirect('ageis_app:user_profile')
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:user_profile')
    
def delete_qualification_view(request, qualification_id):
    try:
        user_type = request.user.extenedusermodel.user_type 
        
        qualification = get_object_or_404(Qualification, id=qualification_id)
        qualification.delete()
        if user_type == 'user':
            messages.success(request, 'Qualification deleted successfully.')
        else:
            return JsonResponse({'status': 'success', 'message': 'Qualification deleted successfully.'})

    except Exception as e:
        print(f"An error occurred: {e}")
        if user_type == 'user':
            messages.error(request, 'An unexpected error occurred while trying to delete the qualification. Please try again later.')
        else:
            return JsonResponse({'status': 'error','message': 'An unexpected error occurred while trying to delete the qualification. Please try again later.'})
    return redirect('ageis_app:user_profile')
    



def add_qualification_view(request):
    try:
        user_profile = ExtendedUserModel.objects.get(user=request.user)
        
        if request.method == 'POST':
            print('Post')
            completion_year = request.POST.get('year', '')
            institution = request.POST.get('university', '')
            degree = request.POST.get('qulification', '')  # Fixed typo here

            # Validate the inputs
            if not all([degree, institution, completion_year]):
                messages.error(request, "All fields are required.")
                return redirect('ageis_app:user_profile')  # Redirect to profile page with error message
            
            # Create the new qualification
            Qualification.objects.create(
                user=user_profile,
                degree=degree,
                institution=institution,
                completion_year=completion_year
            )
            messages.success(request, "Qualification added successfully.")
            return redirect('ageis_app:user_profile')

        else:
            form = ExtendedUserModelForm(instance=user_profile)
        
        return render(request, 'user_profile.html', {'form': form})

    except ExtendedUserModel.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('ageis_app:user_profile')  # Redirect to profile page with error message
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:user_profile') 

def delete_skill_view(request, skill_id):
    try:
        user_type = request.user.extenedusermodel.user_type 
        skill = get_object_or_404(Skills, id=skill_id)
        skill.delete()
        if user_type == 'user':
            messages.success(request, 'Skill deleted successfully.')
        else:
            return JsonResponse({'status': 'success', 'message': 'Skill deleted successfully.'})
    except Exception as e:
        print(f"An error occurred: {e}")
        if user_type == 'user':
            messages.error(request, 'An unexpected error occurred while deleting the skill. Please try again later.')
        else:
            return JsonResponse({'status': 'error','message': 'An unexpected error occurred while deleting the skill. Please try again later.'})
    return redirect('ageis_app:user_profile')

def add_skill(request):
    try:
        # Ensure user profile exists
        user_profile = ExtendedUserModel.objects.get(user=request.user)

        if request.method == 'POST':
            skill_data = request.POST.get('skill', '')

            if not skill_data:
                messages.error(request, "No skills provided. Please enter at least one skill.")
                return redirect('ageis_app:user_profile')


            skills = [skill.strip() for skill in skill_data.split(',') if skill.strip()]


            for skill in skills:
                Skills.objects.create(
                    user=user_profile, 
                    skill=skill,
                )

            messages.success(request, "Skills added successfully.")
            return redirect('ageis_app:user_profile')

        else:
            form = ExtendedUserModelForm(instance=user_profile)

    except ExtendedUserModel.DoesNotExist:
        messages.error(request, "User profile not found. Please contact support.")
        return redirect('ageis_app:user_profile')
    
    except Exception as e:
        print(f"An error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:user_profile')



def add_experience_view(request):
    if request.method == 'POST':
        try:
            company = request.POST.get('experience-com')
            position = request.POST.get('experience-position')
            start_date_str = request.POST.get('experience-start-date')
            end_date_str = request.POST.get('experience-end-date')
            details = request.POST.get('experience-details')

            if not all([company, position, start_date_str, details]):
                messages.error(request, 'Please fill out all required fields.')
                return redirect('ageis_app:user_profile')

            try:
                start_date = parse_date(start_date_str)
                end_date = parse_date(end_date_str) if end_date_str else None
                if not start_date:
                    raise ValueError('Invalid start date format.')
            except (ValueError, TypeError) as e:
                messages.error(request, f'Error with date format: {e}')
                return redirect('ageis_app:user_profile')

            Experience.objects.create(
                user=request.user.extenedusermodel,
                company=company,
                position=position,
                start_date=start_date,
                end_date=end_date,
                description=details
            )
            messages.success(request, 'Experience added successfully.')
            return redirect('ageis_app:user_profile')

        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, "An unexpected error occurred. Please try again later.")
            return redirect('ageis_app:user_profile')

    return redirect('ageis_app:user_profile')



@login_required(login_url='ageis_app:login')
def change_resume_view(request):
    try:
        if request.method == 'POST':
            if 'resume' in request.FILES:
                # Get the user's profile
                user_profile, created = ExtendedUserModel.objects.get_or_create(user=request.user)
                
                # Update the CV field
                user_profile.cv = request.FILES['resume']
                user_profile.save()
                
                messages.success(request, 'Resume updated successfully.')
                return redirect('ageis_app:user_profile')
            else:
                messages.error(request, 'No resume file was uploaded.')
        
        return render(request, 'change_resume.html')

    except ExtendedUserModel.DoesNotExist:
        messages.error(request, 'User profile does not exist.')
        return redirect('ageis_app:user_profile')
    
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        # Add an error message to be displayed on the error page
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:user_profile')


def delete_experience_view(request, experience_id):

    user_type = request.user.extenedusermodel.user_type 
    
    try:
        experience = get_object_or_404(Experience, id=experience_id)
        experience.delete()
        if user_type == 'user':
            return redirect('ageis_app:user_profile')
        else:
            return JsonResponse({'status':'success','message': 'Experience deleted successfully.'})
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})


    
    
@login_required
def add_language(request):
    if request.method == 'POST':
        language_names = request.POST.get('language', '')

        if not language_names:
            messages.error(request, "No languages provided. Please enter at least one language.")
            return redirect('ageis_app:user_profile')
        
        # Split the language names by commas and strip any extra whitespace
        language_list = [lang.strip() for lang in language_names.split(',') if lang.strip()]

        try:
            # Create a Language object for each name
            for language_name in language_list:
                Language.objects.create(user=request.user, language=language_name)

            messages.success(request, "Languages added successfully.")
        except Exception as e:
            # Log the exception or handle it as needed
            print(f"An error occurred while adding languages: {e}")
            messages.error(request, "An unexpected error occurred while adding languages. Please try again later.")
        
        return redirect('ageis_app:user_profile')

    # Redirect if request method is not POST
    return redirect('ageis_app:user_profile')
   
@login_required
def delete_language(request, language_id):
    try:
        user_type = request.user.extenedusermodel.user_type
        if user_type == 'user':

            language = get_object_or_404(Language, id=language_id, user=request.user)
            language.delete()
            messages.success(request, 'Language deleted successfully.')

        else:
            language = get_object_or_404(Language, id=language_id)
            language.delete()
            return JsonResponse({'status': 'success', 'message': 'Language deleted successfully.'})
    except Exception as e:
        
        print(f"An error occurred: {e}")
        
        if user_type == 'user':
            messages.error(request, 'An unexpected error occurred while trying to delete the language. Please try again later.')
        else:
            return JsonResponse({'status': 'error', 'message': 'An error occurred while deleting the Language. Please try again.'}, status=500)
    return redirect('ageis_app:user_profile')


@login_required
def staff_list(request):
    try:
    # Check if the user is authorized to access this view
        if request.user.extenedusermodel.user_type not in ['manager', 'owner']:
            return HttpResponseForbidden("You are not authorized to access this page.")
        user_type = request.user.extenedusermodel.user_type 
        # Determine if the user is an owner
        is_owner = request.user.extenedusermodel.user_type == 'owner'

        # Fetch staff members
        if is_owner:
            staff_members = User.objects.filter(extenedusermodel__user_type__in=['staff', 'manager'])
        else:
            staff_members = User.objects.filter(extenedusermodel__user_type='staff')

        if request.method == 'POST':
            if 'create_staff' in request.POST:
                username = request.POST['username']
                email = request.POST['email']
                password = request.POST['password']
                first_name = request.POST['first_name']
                last_name = request.POST['last_name']


                user = User.objects.create_user(username=username, email=email, password=password)
                user.is_staff = True
                user.first_name = first_name
                user.last_name = last_name
                user.save()

                phone = request.POST.get('phone')
                profile_photo = request.FILES.get('profile_photo')
                gender = request.POST.get('gender')
                dob = request.POST.get('dob')
                address = request.POST.get('address')
                user_type = request.POST['user_type']

                # Create associated extended user model
                ExtendedUserModel.objects.create(
                    user=user,
                    user_type=user_type,
                    phone=phone,
                    profile_photo=profile_photo,
                    gender=gender,
                    dob=dob,
                    address=address
                )

            elif 'edit_staff' in request.POST:
                staff_id = request.POST['staff_id']
                staff_member = get_object_or_404(User, id=staff_id)
                staff_member.username = request.POST['username']
                staff_member.email = request.POST['email']
                password = request.POST.get('password')
                staff_member.first_name = request.POST['first_name']
                staff_member.last_name = request.POST['last_name']
                if password:
                    staff_member.set_password(password)

                staff_member.save()

                extended_user = staff_member.extenedusermodel
                extended_user.phone = request.POST.get('phone', extended_user.phone)
                extended_user.gender = request.POST.get('gender', extended_user.gender)
                extended_user.dob = request.POST.get('dob', extended_user.dob)
                extended_user.address = request.POST.get('address', extended_user.address)
                extended_user.user_type = request.POST.get('user_type', extended_user.user_type) 
                
                if 'profile_photo' in request.FILES:
                    extended_user.profile_photo = request.FILES['profile_photo']

                extended_user.save()

            return redirect('ageis_app:staff_list')
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:error_page')  # Redirect to a custom error page

    return render(request, 'staff_list.html', {
        'staff_members': staff_members,
        'is_owner': is_owner,
        'user_type':user_type
    })


@login_required
def delete_staff(request, staff_id):
    try:
        # Retrieve the staff member
        staff_member = get_object_or_404(User, id=staff_id)

        # Delete the staff member
        staff_member.delete()

        # Success message
        messages.success(request, 'Staff member deleted successfully.')
        return redirect('ageis_app:staff_list')

    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred while deleting staff member: {e}")
        
        # Add an error message to be displayed to the user
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return redirect('ageis_app:staff_list')  # Redirect back to the staff list


def block_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = False  # Optionally also deactivate the user account
        user.save()
        messages.success(request, f'{user.username} has been blocked successfully.')
    except ObjectDoesNotExist:
        messages.error(request, "The specified user does not exist.")
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred while blocking the user: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
    
    return redirect('ageis_app:user_management')





def unblock_user(request, user_id):
    try:
        if not request.user.has_perm('app_name.can_unblock_user'):
            raise PermissionDenied("You do not have permission to unblock users.")
        
        user = get_object_or_404(User, id=user_id)
        
        if user.is_active:
            messages.info(request, f'{user.username} is already active.')
        else:
            user.is_active = True
            user.save()
            messages.success(request, f'{user.username} has been unblocked.')
    
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('ageis_app:user_management')
    
    except DatabaseError as e:
        print(f"Database error: {e}")
        messages.error(request, "A database error occurred. Please try again later.")
        return redirect('ageis_app:user_management')
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('ageis_app:user_management')
    
    return redirect('ageis_app:user_management')