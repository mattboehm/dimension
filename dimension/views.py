# -*- coding: utf-8 -*-
from __future__ import division
from . import models
from ._builtin import Page, WaitPage

from django.http import HttpResponse
from django.views.generic import View


def vars_for_all_templates(self):
    return {'instructions': 'dimension/Instructions.html'}


class Begin(Page):
    template_name = 'dimension/Begin.html'

    def is_displayed(self):
        return ((self.subsession.round_number == 1) & 
            (models.Constants.show_instructions))

class PRA(Page):
    template_name = 'dimension/PRA.html'

    def vars_for_template(self):
        self.group.set_identifier()

    def is_displayed(self):
        return ((self.subsession.round_number == 1) & 
            (models.Constants.show_instructions))


class Introduction(Page):
    template_name = 'dimension/Introduction.html'

    def vars_for_template(self):
        return {'num_rounds': models.Constants.num_rounds, 
        'num_games' : models.Constants.num_games}

    def is_displayed(self):
        return models.Constants.show_instructions

class IntroductionPayment(Page):
    template_name = 'dimension/IntroductionPayment.html'

    def vars_for_template(self):
        return {'redeem_value': models.Constants.redeem_value,
        'tokens_per_cent': models.Constants.tokens_per_cent,
        'tokens_per_dollar' : models.Constants.tokens_per_cent*100,
        'starting_tokens' : models.Constants.starting_tokens}

    def is_displayed(self):
        return models.Constants.show_instructions

class IntroductionRoles(Page):
    template_name = 'dimension/IntroductionRoles.html'

    def vars_for_template(self):
        return {'redeem_value': models.Constants.redeem_value,
        }

    def is_displayed(self):
        return models.Constants.show_instructions

class AssignedDirections(Page):
    template_name = 'dimension/AssignedDirections.html'

    def vars_for_template(self):
        return {'rounds_per_game': models.Constants.rounds_per_game,
        }

    def is_displayed(self):
        return models.Constants.show_instructions

class SellerInstructions(Page):
    template_name = 'dimension/SellerInstructions.html'

    def vars_for_template(self):
        return {'buyers_per_group': self.subsession.buyers_per_group,
        'num_other_sellers': self.subsession.sellers_per_group-1,
        'num_prices' : self.subsession.num_prices,
        'production_cost' : models.Constants.production_cost}

    def is_displayed(self):
        return models.Constants.show_instructions

class SellerQ1(Page):
    template_name = 'dimension/SellerQ1.html'
    form_model = models.Player
    form_fields = ['quiz_q1']

    def is_displayed(self):
        return models.Constants.show_instructions

class SellerQ1Ans(Page):
    template_name = 'dimension/SellerQ1Ans.html'

    def is_displayed(self):
        return models.Constants.show_instructions

    def vars_for_template(self):
        return {'correct_answer' : '0 tokens'}

class SellerQ2(Page):
    template_name = 'dimension/SellerQ2.html'
    form_model = models.Player
    form_fields = ['quiz_q2']

    def is_displayed(self):
        return models.Constants.show_instructions

class SellerQ2Ans(Page):
    template_name = 'dimension/SellerQ2Ans.html'

    def is_displayed(self):
        return models.Constants.show_instructions

    def vars_for_template(self):
        return {'correct_answer' : 'It depends on the prices I set'}

class BuyerInstructions(Page):
    template_name = 'dimension/BuyerInstructions.html'

    def is_displayed(self):
        return models.Constants.show_instructions

class RoundSummaryExample(Page):
    template_name = 'dimension/RoundSummaryExample.html'

    def is_displayed(self):
        return models.Constants.show_instructions

class Intro(Page):
    template_name = 'dimension/Intro.html'

class SetPrices(Page):
    template_name = 'dimension/SetPrices.html'
    form_model = models.Player

    def is_displayed(self):
        return self.player.role_int == 1

    def get_form_fields(self):
        return [
            'seller_price{}'.format(i)
            for i in range(self.subsession.num_prices)
        ]

    def vars_for_template(self):
        return {'num_prices': self.subsession.num_prices,
        'role' : self.player.role,
        'role_int' : self.player.role_int}

    def error_message(self, value):
        # Take all prices the user did not set and make them numeric and zero
        for i, inputs in enumerate(value):
            if value[inputs] == None:
                value[inputs] = 0
        # Check that the sum of prices is less than the maximum total price allowed
        if sum(value.values()) > models.Constants.max_total_price:
            return "The sum of all prices must be less than or equal to {}".format(
                models.Constants.max_total_price)


class SelectSeller(Page):
    template_name = 'dimension/SelectSeller.html'
    form_model = models.Player
    form_fields = ('buyer_choice',)

    def seller1_prices(self):
        # Fix 16 to variable
        sellers = [p for p in self.group.get_players() if p.role_int==1]
        seller1 = sellers[sellers.identifier==1]
        prices1 = [0]*16
        for i in max(Constants.prices_per_seller):
            exec("prices1[%d] = seller1.seller_price%s" % (i))

    def seller2_prices(self): 
        # Fix 16 to variable
        sellers = [p for p in self.group.get_players() if p.role_int==1]
        seller2 = sellers[sellers.identifier==2]
        prices2 = [0]*16
        for i in max(Constants.prices_per_seller):
            exec("prices2[%d] = seller2.seller_price%s" % (i))

    def is_displayed(self):
        return self.player.role_int == 2

    def vars_for_template(self):
        return {
            'sellers': sorted(filter(
                lambda p: 1 == p.role_int,
                self.group.get_players()), key = lambda p: p.identifier
            ), 'num_prices' : self.subsession.num_prices,
        }


class SetPricesWaitPage(WaitPage):
    pass


class BuyerWaitPage(WaitPage):
    # if models.Player.role == 'seller':
    #     template_name = "WaitPage.html"
    # else: 
    #     template_name = 'dimension/BuyerWaitPage.html'
    # # wait_for_all_groups = True
    #template_name = "WaitPage.html"

    def after_all_players_arrive(self):
        self.group.total_cost()
        self.group.buyer_cost()
        self.group.number_sales()
        self.group.calculate_payoff()
        self.group.buyer_choice_to_seller_selected()


    
class RoundSummary(Page):
    template_name = 'dimension/RoundSummary.html'

    # print models.player.buyer_choice +1 if models.player.role_int ==2 else models.player.buyer_choice
    def vars_for_template(self):
        return {
        'sellers': sorted(filter(
                lambda p: 1 == p.role_int,
                self.group.get_players()), key = lambda p: p.identifier
            ), 'num_prices' : self.subsession.num_prices,
        'real_round' : self.subsession.is_real_round(),
        'cumulative_payoff' : sum([p.payoff for p in self.player.in_all_rounds()]),
        'buyers' : enumerate(sorted(filter(
            lambda p: 2 == p.role_int, 
            self.group.get_players()), key = lambda p: p.identifier
        ))
        
        }

class RoundSummaryWait(WaitPage):
    #wait_for_all_groups = True

    def after_all_players_arrive(self):
        self.group.adjust_payoff()


page_sequence = [ 
    Begin,
    PRA,
    Introduction,
    IntroductionPayment,
    IntroductionRoles,
    AssignedDirections,
    SellerInstructions,
    SellerQ1,
    SellerQ1Ans,
    SellerQ2,
    SellerQ2Ans,
    BuyerInstructions,
    RoundSummaryExample,
    Intro,
    SetPrices,
    SetPricesWaitPage,
    SelectSeller,
    BuyerWaitPage,
    RoundSummary,
    RoundSummaryWait,
]

### All of these pages will go into a survey app
# SurveyExperience
# Numeracy
# RiskQ1,
# RiskQ2or3,
# RiskQ4
# Gender
# EndExperiment


class ClickView(View):
    def get(self, request):
        player_id = request.GET.get('player_id')

        try:
            player = models.Player.objects.get(pk=player_id)
        except models.Player.DoesNotExist:
            return HttpResponse('something went wrong')

        clicks = player.add_click()
        return HttpResponse('{} click(s)'.format(clicks))
