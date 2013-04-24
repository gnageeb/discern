from django.db import models
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.db.models.signals import post_save, pre_save
import random
import string
from django.conf import settings
import requests
import json
import logging

log= logging.getLogger(__name__)

class Rubric(models.Model):
    associated_problem = models.IntegerField()
    user = models.ForeignKey(User)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def get_scores(self):
        scores = []
        all_scores = []
        final_score=0
        max_score = 0
        options = self.get_rubric_dict()
        for option in options:
            all_scores.append(option['option_points'])
            if option['selected']:
                scores.append(option['option_points'])

        if len(scores)>0:
            final_score = sum(scores)

        if len(all_scores)>0:
            max_score = sum(all_scores)

        return {
            'score' : final_score,
            'max_score' : max_score
        }

    def get_rubric_dict(self):
        options = []
        option_set = self.rubricoption_set.all().order_by('id')
        for option in option_set:
            options.append(model_to_dict(option))
        return options

class RubricOption(models.Model):
    rubric = models.ForeignKey(Rubric)
    option_points = models.IntegerField()
    option_text = models.TextField()
    selected = models.BooleanField(default=False)

class UserProfile(models.Model):
    api_pass = models.TextField()
    api_user = models.TextField()
    api_user_created = models.BooleanField(default=False)

def api_create_callback(sender, instance, **kwargs):
    random_pass = ''.join([random.choice(string.digits + string.letters) for i in range(0, 15)])
    data = {
        'username' : instance.username,
        'password' : random_pass,
    }

    headers = {'content-type': 'application/json'}

    #Now, let's try to get the schema for the create user model.
    create_user_url = settings.API_URL_BASE + "/essay_site/api/v1/createuser/"
    counter = 0
    status_code = 400

    while status_code==400 and counter<2:
        try:
            response = requests.post(create_user_url, data=json.dumps(data),headers=headers)
            status_code = response.status_code
            if status_code==201:
                instance.profile.api_user_created = True
                instance.profile.api_pass = data['password']
                instance.profile.api_user = data['username']
                instance.profile.save()
        except:
            log.error("Could not create an API user!")
            instance.profile.api_user_created = False
            instance.profile.save()
        counter+=1
        data['username'] += random.choice(string.digits + string.letters)

post_save.connect(api_create_callback, sender=User)

#Maps the get_profile() function of a user to an attribute profile
User.profile = property(lambda u: u.get_profile())