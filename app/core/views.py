from core.decorators import require_party_login
from core.forms import PoliticianForm, PartyPoliticianForm, RegistrationForm
from core.models import Politician, Question, Answer, Candidacy, Mandate, Constituency, Language
from core.models import Statistic, Category, Link, Party
from core.tools import set_cookie, get_cookie, send_mail_to_politician
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView

from textwrap import dedent
from easy_thumbnails.files import get_thumbnailer
from meta.views import Meta
from urllib.parse import urlencode
from re import split
import collections
import csv
import json

##
# ERROR VIEWS
##


def handler404(request):
    response = render(request, '404.html')
    response.status_code = 404

    return response


def handler500(request):
    response = render(request, '500.html')
    response.status_code = 500

    return response

##
# GENERIC META
##


default_meta = Meta(
    title = 'Freedomvote',
    description = _('The platform for freedom, technology and politics'),
    image = '/static/images/logo.png'
)

##
# PUBLIC VIEWS
##


def initial_edit_view(request, lang):
    if settings.DEBUG:
        response = render(request, 'core/initial_edit.html')
    else:
        response = render(request, '404.html')
        response.status_code = 404
    return response


def candidates_view(request):
    constituencies  = Constituency.objects.all().order_by('name')
    parties         = Party.objects.all().order_by('name')
    categories      = (
        Category.objects.filter(statistic__id__gt=0).
        order_by('name').distinct())
    mandates        = Mandate.objects.all()

    constituency = request.GET.get('constituency', None)
    category = request.GET.get('category', None)
    search   = request.GET.get('search', None)

    session_answers    = get_cookie(request, 'answers',    {})
    session_statistics = get_cookie(request, 'statistics', {})
    
    has_cookie = len(session_answers) > 0 and len(session_statistics) > 0

    context = {
        'categories'    : categories,
        'parties'       : parties,
        'meta'          : default_meta,
        'has_cookie'    : has_cookie,
        'mandates'      : mandates,
        'constituencies': constituencies
    }

    if has_cookie:
        query_params = {}

        for k, v in session_statistics.items():
            query_params['statistics_{0}'.format(k)] = v

        for k, v in session_answers.items():
            query_params['answers_{0}'.format(k)] = v

        formatted_query_params = urlencode(query_params)
        
        context['share_url'] = '{0}/share?{1}'.format(
            settings.BASE_URL,
            formatted_query_params
        )

    return render(
        request,
        'core/candidates/index.html',
        context
    )


def compare_view(request):
    questions = Question.objects.all().order_by('question_number')
    data      = []

    session_answers    = get_cookie(request, 'answers',    {})
    session_statistics = get_cookie(request, 'statistics', {})

    if request.method == "POST":
        for question in questions:
            qid = 'question_%d' % question.id
            session_answers[qid] = request.POST.get(qid, 0)

        categories = Category.objects.all()

        for category in categories:
            cq = Question.objects.filter(category=category)

            if not len(cq):
                continue

            values = []
            for question in cq:
                values.append(
                    abs(
                        question.preferred_answer -
                        int(session_answers.get(
                            'question_%d' % question.id, 0))
                    )
                )
            session_statistics['category_%d' % category.id] = (
                10 - sum(values) / float(len(cq)))

        request.COOKIES['answers'] = session_answers
        request.COOKIES['statistics'] = session_statistics
        messages.success(request, _('answers_saved_successfully_evaluate'))

    for question in questions:
        item = {
            'question' : question,
            'value'    : session_answers.get('question_%d' % question.id, 0)
        }
        data.append(item)

    if request.method == "GET":
        response = render(
            request,
            'core/compare/index.html',
            {
                'data' : data,
                'meta' : default_meta
            }
        )

    else:
        response = redirect('%s?evaluate=1' % reverse('candidates'))

    set_cookie(response, 'answers', session_answers, 30)
    set_cookie(response, 'statistics', session_statistics, 30)
    return response


def share_view(request):
    response = redirect('%s?evaluate=1' % reverse('candidates'))

    cookies = {
        'statistics': {},
        'answers'   : {}
    }

    for k, v in request.GET.items():
        if '_' in k:
            cookie_name, variable_name = split('_', k, maxsplit=1) 
            # V can be a float or int in a string and since we can not
            # parse a float in a string to int we did it this way
            cookies[cookie_name][variable_name] = int(float(v))
        else:
            continue

    set_cookie(response, 'answers', cookies['answers'], 30)
    set_cookie(response, 'statistics', cookies['statistics'], 30)
    return response


def compare_reset_view(request):
    messages.success(request, _('answers_resetted'))

    response = HttpResponseRedirect(reverse('compare'))

    set_cookie(response, 'answers', {}, 30)
    set_cookie(response, 'statistics', {}, 30)

    return response

##
# PUBLIC POLITICIAN VIEWS
##


def politician_view(request, politician_id):
    politician = get_object_or_404(
        Politician.objects.filter(statistic__id__gt=0).distinct(),
        pk=politician_id)

    answers    = (
        Answer.objects.
        filter(politician=politician).
        order_by('question__question_number'))
    links      = (
        Link.objects.filter(politician=politician))
    cookie     = get_cookie(request, 'answers', {})
    answer_obs = []
    candidacies = Candidacy.objects.filter(politician=politician).order_by('-constituency')

    for a in answers:
        answer_obs.append({
            'own_ans': cookie.get('question_%s' % a.question.id, None),
            'politician_ans': a
        })
    embed_url_reverse = reverse('politician_statistic_spider_embed', kwargs={'politician_id' : politician_id})
    embed_url_absolute = request.build_absolute_uri(embed_url_reverse)

    meta = Meta(
        title=u'{0} {1}'.format(politician.first_name, politician.last_name),
        image=get_thumbnailer(politician.image)['large'].url if politician.image else None,
        description=_("%(first_name)s %(last_name)s on Freedomvote") % { 'first_name': politician.first_name, 'last_name': politician.last_name },
        url=request.build_absolute_uri(reverse('politician', kwargs={'politician_id':politician.id}))
    )

    return render(
        request,
        'core/profile/index.html',
        {
            'politician'     : politician,
            'answers'        : answer_obs,
            'links'          : links,
            'embed_url'      : embed_url_absolute,
            'meta'           : meta,
            'base_url'       : settings.BASE_URL,
            'candidacies'    : candidacies
        }
    )


def politician_statistic_spider_view(request, politician_id):
    statistics = Statistic.get_statistics_by_politician(politician_id)
    stats      = get_cookie(request, 'statistics', {})
    values     = {
        'politician' : [s.accordance for s in statistics],
        'citizen'    : [
            stats.get('category_%d' % s.category.id, 0)
            for s in statistics]
    }

    return JsonResponse({
        'categories': [
            s.category.name
            for s in statistics
        ],
        'values': values
    })


def politician_statistic_spider_view_embed(request, politician_id):
    statistics = Statistic.get_statistics_by_politician(politician_id)

    politician_url_reverse = reverse('politician', kwargs={'politician_id' : politician_id})
    politician_url_absolute = request.build_absolute_uri(politician_url_reverse)

    return render(
        request,
        'core/profile/spider_embed.html',
        {
            'politician_id': politician_id,
            'politician_url': politician_url_absolute
        }
    )


def politician_statistic_view(request, politician_id):
    category_id = int(request.GET.get('category', False))
    titles  = [force_text(_('total'))]

    if category_id:
        category = get_object_or_404(Category, id=category_id)
        titles.append(category.name)

    if 'evaluate' in request.GET:
        cat_by_id = {
            cat.id: cat
            for cat
            in Category.objects.all()
        }

        pol_answers = Answer.objects.filter(politician_id=politician_id)
        pairs = []
        answers    = get_cookie(request, 'answers',    {})

        delta_by_cat = collections.defaultdict(lambda: [])
        for ans in pol_answers:
            voter_value = int(answers.get('question_%s' % ans.question_id, 0))
            delta       = abs(ans.agreement_level - voter_value)
            delta_by_cat[ans.question.category_id].append(delta)

        for cid, cat in cat_by_id.items():
            if not len(delta_by_cat[cid]):
                continue

            pairs.append({
                'category': cat.name,
                'value':    (
                    10 - sum(delta_by_cat[cid]) /
                    float(len(delta_by_cat[cid]))
                )
            })

        sorted_pairs = sorted(pairs, key=lambda k: k['category'])

        detail = {
            'categories' : [i['category'] for i in sorted_pairs],
            'values'     : [i['value']    for i in sorted_pairs]
        }

        total = sum(detail['values']) / len(detail['values'])
        pos     = [total]
        neg     = [(10 - total)]

        if category_id:
            val = 10 - (
                sum(delta_by_cat[category_id]) /
                float(len(delta_by_cat[category_id])))
            pos.append(val)
            neg.append(10 - val)

        summary = {
            'titles' : titles,
            'values' : {
                'positive' : pos,
                'negative' : neg
            }
        }

    else:
        statistics = Statistic.get_statistics_by_politician(politician_id)
        values  = [s.accordance for s in statistics]
        total   = sum(values) / len(values)

        # pos is the green part (agreement level) of the graph,
        # neg is the "rest" (red)
        pos     = [total]
        neg     = [(10 - total)]

        if category_id:
            # if category_id is given, the graph should display this
            # category in addition to the summary view
            statistic = Statistic.objects.get(
                politician_id=politician_id, category=category)
            pos.append(statistic.value / 10)
            neg.append(10 - statistic.value / 10)

        summary = {
            'titles' : titles,
            'values' : {
                'positive' : pos,
                'negative' : neg
            }
        }

        detail  = {
            'categories' : [s.category.name for s in statistics],
            'values'     : values
        }

    return JsonResponse({'summary': summary, 'detail': detail})

##
# PRIVATE POLITICIAN VIEWS
##


def politician_edit_view(request, unique_key):
    return redirect(reverse('politician_edit_profile', args=[unique_key]))


def politician_edit_profile_view(request, unique_key):
    politician = get_object_or_404(Politician, unique_key=unique_key)

    links      = (
        Link.objects.filter(politician=politician))

    if request.POST:
        form = PoliticianForm(request.POST, request.FILES, instance=politician)
        if form.is_valid():
            form.save()
            messages.success(request, _('profile_saved_successfully'))
    else:
        form = PoliticianForm(instance=politician)

    return render(
        request,
        'core/edit/profile.html',
        {
            'politician' : politician,
            'form'       : form,
            'links'      : links
        }
    )


def politician_edit_questions_view(request, unique_key):
    politician = get_object_or_404(Politician, unique_key=unique_key)
    questions  = Question.objects.all().order_by('question_number')
    answers    = Answer.objects.filter(politician=politician)

    return render(
        request,
        'core/edit/questions.html',
        {
            'politician' : politician,
            'questions'  : questions,
            'answers'    : answers
        }
    )


def politician_edit_candidacies_view(request, unique_key):
    if request.method == "GET":
        politician = get_object_or_404(Politician, unique_key=unique_key)
        candidacies  = Candidacy.objects.filter(politician=politician)
        mandates = Mandate.objects.all()
        mandates_candidacies = {}
        mandates_constituencies = {}

        for mandate in mandates:
            try:
                answer = Candidacy.objects.filter(politician=politician, mandate=mandate).first()
                constituency = Constituency.objects.filter(mandate=mandate).all().order_by('name')
            except Candidacy.DoesNotExist:
                answer = None

            mandates_candidacies.update({mandate: answer})
            mandates_constituencies.update({mandate: constituency})

        return render(
            request,
            'core/edit/candidacies.html',
            {
                'politician': politician,
                'mandates_candidacies': mandates_candidacies,
                'mandates_constituencies': mandates_constituencies
            }
        )
    elif request.method == "POST":
        mandate = get_object_or_404(Mandate, id=request.POST.get('mandate'))
        politician = get_object_or_404(Politician, unique_key=unique_key)
        answer = request.POST.get('answer')
        constituency = request.POST.get('constituency')

        try:
            candidacy = Candidacy.objects.get(id=request.POST.get('candidacy'))
        except Candidacy.DoesNotExist:
            candidacy = Candidacy(mandate=mandate)
            constituency = Constituency.objects.filter(mandate=mandate).order_by('name').first()
        
        if answer == "no_candidacy":
            candidacy = Candidacy.objects.filter(politician=politician, mandate=mandate)
            candidacy.delete()
        elif answer == "new_candidacy" or answer == "old_candidacy":
            if not isinstance(constituency, Constituency):
                constituency = Constituency.objects.filter(id=request.POST.get('constituency')).first()
            if answer == "new_candidacy":
                candidacy.is_new = True
            else:
                candidacy.is_new = False
            candidacy.constituency = constituency
            candidacy.save()
            politician.candidacy.add(candidacy)     

        messages.success(request, _('candidacy_saved_successfully'))

        return redirect(reverse('politician_edit_candidacies', args=[unique_key]))


def politician_answer_view(request, unique_key):
    if request.POST:
        question = get_object_or_404(Question, id=request.POST.get('question'))
        politician = get_object_or_404(Politician, unique_key=unique_key)
        agreement_level = int(request.POST.get('agreement_level', 0))

        answer, created = Answer.objects.get_or_create(
            question=question,
            politician=politician,
            defaults={
                'agreement_level' : agreement_level,
            }
        )
        answer.agreement_level = agreement_level
        answer.note = request.POST['note']
        answer.save()

    return HttpResponse('')


def politician_publish_view(request, unique_key):
    politician = get_object_or_404(Politician, unique_key=unique_key)
    categories = Category.objects.all()

    for category in categories:
        answers = Answer.objects.filter(
            question__category=category, politician=politician)
        if answers:
            answers_agg = answers.aggregate(Sum('agreement_level'))
            value = int(
                answers_agg['agreement_level__sum'] /
                answers.count() * 10)
            stat, created = Statistic.objects.get_or_create(
                politician=politician,
                category=category,
                defaults={'value': value}
            )
            stat.value = value
            stat.save()

    return JsonResponse({
        'type': 'success',
        'text': force_text(_('answers_published_successfully'))
    })


def politician_unpublish_view(request, unique_key):
    politician = get_object_or_404(Politician, unique_key=unique_key)
    Statistic.objects.filter(politician=politician).delete()

    return JsonResponse({
        'type': 'success',
        'text': force_text(_('answers_unpublished_successfully'))
    })


def politician_link_add_view(request, unique_key):
    politician = get_object_or_404(Politician, unique_key=unique_key)
    url        = request.POST.get('url')
    error      = False

    if not url.startswith(('http://', 'https://')):
        url = 'http://%s' % url

    if '.' not in url:
        error = True

    if not error:
        l = Link(
            politician=politician,
            url=url
        )
        l.save()
        url = ''

    links      = (
        Link.objects.filter(politician=politician))

    return render(request, 'core/edit/links.html', {
        'links'      : links,
        'politician' : politician,
        'error'      : error,
        'input'      : url
    })


def politician_link_delete_view(request, unique_key, link_id):
    politician = get_object_or_404(Politician, unique_key=unique_key)
    link = get_object_or_404(Link, id=link_id)
    link.delete()

    links      = (
        Link.objects.filter(politician=politician))

    return render(request, 'core/edit/links.html', {
        'links'      : links,
        'politician' : politician
    })

##
# PARTY VIEWS
##


def party_login_view(request, party_name):
    user = get_object_or_404(User, username=party_name)

    if request.user.is_authenticated() and request.user.username == party_name:
        return redirect(reverse('party_dashboard', args=[party_name]))

    if request.POST:
        user = authenticate(
            username=party_name, password=request.POST.get('password'))
        if user and user.is_active:
            login(request, user)
            messages.success(request, _('login_successful'))
            return redirect(reverse('party_dashboard', args=[party_name]))
        else:
            messages.error(request, _('login_error'))

    return render(request, 'core/party/login.html')


def party_logout_view(request, party_name):
    logout(request)

    return redirect(settings.BASE_URL)


@require_party_login
def party_dashboard_view(request, party_name):
    return render(
        request,
        'core/party/dashboard.html',
        {
            'politicians': Politician.objects.filter(user=request.user)
        }
    )


@require_party_login
def party_politician_add_view(request, party_name):
    request.POST._mutable = True
    if request.POST:
        form = PartyPoliticianForm(request.POST, request.FILES)
        form.data['user'] = request.user.id
        if form.is_valid():
            form.save()
            messages.success(request, _('politician_add_success'))
            return redirect(reverse('party_dashboard', args=[party_name]))
        else:
            messages.error(request, _('politician_add_error'))

    else:
        form = PartyPoliticianForm()

    return render(
        request,
        'core/party/politician_edit.html',
        {
            'politician' : None,
            'form'       : form
        }
    )


@require_party_login
def party_politician_edit_view(request, party_name, politician_id):
    politician = get_object_or_404(Politician, id=politician_id)

    request.POST._mutable = True
    if request.POST:
        form = PartyPoliticianForm(
            request.POST, request.FILES, instance=politician)
        form.data['user'] = request.user.id
        if form.is_valid():
            form.save()
            messages.success(request, _('politician_edit_success'))
            return redirect(reverse('party_dashboard', args=[party_name]))
        else:
            messages.error(request, _('politician_edit_error'))

    else:
        form = PartyPoliticianForm(instance=politician)

    return render(
        request,
        'core/party/politician_edit.html',
        {
            'politician' : None,
            'form'       : form
        }
    )
    pass


@require_party_login
def party_export_view(request, party_name):
    politicians = Politician.objects.filter(user=request.user)

    response = HttpResponse(content_type='text/csv')

    response['Content-Disposition'] = (
        'attachment; filename="freedomvote_export_%s.csv"' % party_name
    )

    writer = csv.writer(response)
    writer.writerow([
        force_text(_('first_name')),
        force_text(_('last_name')),
        force_text(_('unique_url'))
    ])

    for p in politicians:
        cols = [p.first_name, p.last_name, p.unique_url]
        writer.writerow([c.encode('latin1')
                        if c is not None else '' for c in cols
                         ])

    return response


@require_party_login
def party_politician_delete_view(request, party_name, politician_id):
    politician = get_object_or_404(Politician, id=politician_id)
    politician.delete()
    messages.success(
        request, _('politician_delete_success') % (
            politician.first_name, politician.last_name
        ))

    return redirect(reverse('party_dashboard', args=[party_name]))



@require_party_login
def party_import_view(request, party_name):
    return render(
        request,
        'core/party/politicians_import.html'
    )


@require_party_login
def party_upload_csv(request, party_name):
    counter = 0

    try:
        csv = request.FILES["csv_file"]
        data = csv.read().decode("utf-8")
        lines = data.split("\n")

        for line in lines:
            try:
                fields = line.split(",")
                email = fields[2].strip()
                lang = fields[3].strip()
                language = Language.objects.filter(iso_code=lang)

                if Politician.objects.filter(email=email).count() is 0:
                    if language.count() is 0:
                        language = Language(iso_code=lang)
                        language.save()
                    else:
                        language = language.first()

                    politician = Politician.objects.create(
                        first_name = fields[0],
                        last_name = fields[1],
                        email = email,
                        user_id = request.user.id,
                        language = language
                    )

                    politician.save()

                    send_mail_to_politician(request, politician)

                    counter += 1
                else:
                    continue
            except:
                continue

        messages.success(
        request, _('politicians_import_success') % (
            counter
        ))
    except:
        messages.error(request, _('politician_add_error'))

    return redirect(reverse('party_dashboard', args=[party_name]))


@require_party_login
def party_email_view(request, party_name):
    languages = Language.objects.all()
    if request.method == 'GET':
        return render(
            request,
            'core/party/party_email.html',
            {
                'languages': languages
            }
        )
    else:
        recipients_sel = request.POST.get('recipients', None)
        recipients = []
        subjects = {}
        bodies = {}
        for language in languages:
            subjects.update({language: request.POST.get('subject_' + str(language), None)})
            bodies.update({language: request.POST.get('message_' + str(language), None)})
        else:
            subjects.update({'default': request.POST.get('subject', None)})
            bodies.update({'default': request.POST.get('message', None)})

        questions_count = Question.objects.all().count()
        politicians = Politician.objects.filter().exclude(email='')

        if recipients_sel == 'all':
            for politician in politicians:
                recipients.append(politician)
        elif recipients_sel == 'questionaire_done':
            for politician in politicians:
                if Answer.objects.filter(politician_id=politician.id).count() >= questions_count:
                    recipients.append(politician)
        elif recipients_sel == 'questionaire_open':
            for politician in politicians:
                if Answer.objects.filter(politician_id=politician.id).count() < questions_count:
                    recipients.append(politician)

        if len(recipients) is not 0:
            for recipient in recipients:
                if len(languages) > 0:
                    send_mail(
                        subjects[recipient.language].replace('$(first_name)', recipient.first_name).
                                replace('$(last_name)', recipient.last_name),
                        bodies[recipient.language].replace('$(first_name)', recipient.first_name).
                                replace('$(last_name)', recipient.last_name).
                                replace('$(url)', recipient.unique_url),
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient.email],
                        fail_silently=False)
                else:
                    send_mail(
                        subjects['default'].replace('$(first_name)', recipient.first_name).
                                replace('$(last_name)', recipient.last_name),
                        bodies['default'].replace('$(first_name)', recipient.first_name).
                                replace('$(last_name)', recipient.last_name).
                                replace('$(url)', recipient.unique_url),
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient.email],
                        fail_silently=False)

            messages.success(
            request, _('politician_email_sent_successfull') % (
                len(recipients)
            ))
        else:
            messages.error(request, _('politician_email_zero_error'))

        return redirect(reverse('party_dashboard', args=[party_name]))


class PoliticianRegistrationView(FormView):
    model = Politician
    template_name = 'core/candidates/registration.html'
    form_class = RegistrationForm
    success_url = '/registration_send_mail/'

    def get_context_data(self, *args, **kwargs):
        unique_key = self.kwargs['unique_key']
        try:
            User.objects.get(registrationkey__unique_key=unique_key)
        except ObjectDoesNotExist:
            self.template_name = '404.html'
        return super(PoliticianRegistrationView, self).get_context_data(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        request = self.request
        unique_key = self.kwargs['unique_key']
        user = User.objects.get(registrationkey__unique_key=unique_key)
        politician = Politician.objects.create(
            first_name=form.data['first_name'],
            last_name=form.data['last_name'],
            email=form.data['email'],
            user_id=user.id
        )

        send_mail_to_politician(request, politician)

        return super(PoliticianRegistrationView, self).form_valid(form)


class PoliticianRegistrationSendMailView(TemplateView):
    template_name = 'core/candidates/registration_send_mail.html'
