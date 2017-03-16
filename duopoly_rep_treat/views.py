from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants, PriceDim, Ask, Player, Subsession, Group, BaseSubsession
from django.http import JsonResponse, HttpResponse
from statistics import pstdev
from django.shortcuts import render
from . import utils, export
from otree.models.session import Session
from django.contrib.auth.decorators import login_required


# SPLASH PAGE AND PRA
class IntroductionSplash(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_base

class IntroductionPRA(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_base


# INSTRUCTIONS PAGES
class InstructionsBasics(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_base

    def vars_for_template(self):
        return {
            'tokens_per_dollar': int(100./float(self.session.config["real_world_currency_per_point"])),
            'showup': self.session.config['participation_fee'],
        }

class InstructionsBasicsQuiz(Page):
    form_model = models.Player
    form_fields = ['basics_q1']

    def is_displayed(self):
        return self.subsession.show_instructions_base

    def vars_for_template(self):
        return {
            'tokens_per_dollar': int(1. / float(self.session.config["real_world_currency_per_point"])),
        }


class InstructionsRoles(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_base

class InstructionsRolesQuiz(Page):
    form_model = models.Player
    form_fields = ['roles_q1', 'roles_q2']

    def is_displayed(self):
        return self.subsession.show_instructions_base


class InstructionsNewTreatment(Page):

    def is_displayed(self):
        return (self.subsession.show_instructions_base and self.subsession.dims > 1) or \
               (self.subsession.show_instructions_block and not self.subsession.show_instructions_base)


class InstructionsSeller(Page):

    def vars_for_template(self):
        return {'buyers_per_group': Constants.buyers_per_group,
            'num_other_sellers': Constants.sellers_per_group-1,
            # 'num_prices' : self.subsession.dims,
            'production_cost' : Constants.prodcost,
            'price_dims': range(1, self.subsession.dims + 1)
                }

    def is_displayed(self):
        return self.subsession.show_instructions_roles

class InstructionsSellerQuiz(Page):
    form_model = models.Player
    form_fields = ['seller_q1']

    def is_displayed(self):
        return self.subsession.show_instructions_base or self.subsession.treatment_first_multiple


class InstructionsBuyer(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_roles

    def vars_for_template(self):
        return{
            "prices": utils.get_example_prices(self.subsession.dims),
        }

class InstructionsBuyerQuiz(Page):
    form_model = models.Player
    form_fields = ['buyer_q1']

    def is_displayed(self):
        return self.subsession.show_instructions_base


class InstructionsRoundResults(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_base

    def vars_for_template(self):
        player = Player(roledesc="Seller", payoff=225, ask_total=325, numsold=1, rolenum=1)

        return{
            "player": player,
            "subtotal": 225,
            "prices": utils.get_example_prices(self.subsession.dims),
            "s1_ask_total": 325,
            "s2_ask_total": 375,
            "b1_seller": 1,
            "b2_seller": 2,
            "prodcost": 100,
        }

class InstructionsWaitGame(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_base


class PracticeBegin(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_practice

    def vars_for_template(self):
        otherrole = [role for role in ["Buyer", "Seller"] if role != self.player.roledesc][0]
        return {
            "otherrole": otherrole,
        }

class PracticeEnd(Page):

    def is_displayed(self):
        return self.subsession.show_instructions_real




# SELLER PAGE

class ChoiceSeller(Page):

    form_model = models.Player
    form_fields = ['ask_total', 'ask_stdev']


    def is_displayed(self):
        return self.player.roledesc == "Seller"

    def vars_for_template(self):
        round_temp = (self.subsession.round_number - Constants.num_rounds_practice) % Constants.num_rounds_treatment
        round = round_temp if round_temp > 0 else Constants.num_rounds_treatment
        return{
            #'price_dims': self.player.pricedim_set.all()
            "price_dims": range(1, self.subsession.dims+1),
            "round": round
        }

    def before_next_page(self):
        """
            If dims==1 then we need to make and aks object. For the multiple dims case, this is handled when the user
            presses the "distrubute" button or manually edits one of the dim fields.  The dim fields do not exist
            when dims==1.
        """
        if self.subsession.dims == 1:
            player = self.player
            player.create_ask(player.ask_total, pricedims=[player.ask_total], auto=None, manual=None, stdev=0)




# BUYER PAGE

class ChoiceBuyer(Page):

    form_model = models.Player
    form_fields = ['contract_seller_rolenum']

    def is_displayed(self):
        return self.player.roledesc == "Buyer"

    def vars_for_template(self):
        round_temp = (self.subsession.round_number - Constants.num_rounds_practice) % Constants.num_rounds_treatment
        round = round_temp if round_temp > 0 else Constants.num_rounds_treatment
        # if self.subsession.dims > 1:
        prices = zip(range(1, self.subsession.dims + 1),
            [pd.value for pd in self.group.get_player_by_role("S1").get_ask().pricedim_set.all()],
            [pd.value for pd in self.group.get_player_by_role("S2").get_ask().pricedim_set.all()])
        # else:
        #     prices = [[self.group.get_player_by_role("S1").ask_total, self.group.get_player_by_role("S2").ask_total]]
        return {
            "prices": prices,
            "round": round
        }

    def before_next_page(self):
        """ Create bid object.  Set buyer price attributes """
        seller = self.group.get_player_by_role("S" + str(self.player.contract_seller_rolenum))
        ask = seller.get_ask()
        pricedims = [pd.value for pd in ask.pricedim_set.all()]

        bid = self.player.create_bid(ask.total, pricedims)

        self.group.create_contract(bid=bid, ask=ask)
        self.player.set_buyer_data()





# WAIT PAGES

class WaitStartInstructions(WaitPage):
    # This makes sures everyone has cleared the results page before the next round begins
    template_name = 'global/WaitCustom.html'

    wait_for_all_groups = True
    title_text = "Waiting for Other Participants"
    body_text = "Please wait for other participants."


class WaitStartMatch(WaitPage):
    # This makes sures everyone has cleared the instructions pages before the next round begins
    template_name = 'global/WaitCustom.html'

    wait_for_all_groups = True
    title_text = "Waiting for Other Participants"
    body_text = ""


class WaitSellersForSellers(WaitPage):
    template_name = 'global/WaitCustom.html'

    wait_for_all_groups = True
    title_text = "Waiting for Sellers"
    body_text = "You are a buyer. Please wait for the sellers to set their prices."

    def is_displayed(self):
        return self.player.roledesc == "Buyer"


class WaitBuyersForSellers(WaitPage):
    template_name = 'global/WaitCustom.html'

    wait_for_all_groups = True
    title_text = "Waiting for Sellers"
    body_text = "Please wait for the other sellers to set their prices."

    def is_displayed(self):
        return self.player.roledesc == "Seller"

    def after_all_players_arrive(self):
        # When here, sellers have all entered their prices
        # self.group.set_marketvars_seller()
        pass

class WaitGame(WaitPage):
    template_name = 'duopoly_rep_treat/WaitGame.html'

    wait_for_all_groups = True

    form_model = models.Player
    form_fields = ['gamewait_numcorrect']

    def after_all_players_arrive(self):
        pass


class WaitRoundResults(WaitPage):
    # This is just a trigger to calculate the payoffs and market variables before the results page
    template_name = 'global/WaitCustom.html'

    def after_all_players_arrive(self):
        # When here, buyers and sellers have made their choices
        self.group.set_marketvars()


# RESULTS

class RoundResults(Page):
    def vars_for_template(self):
        prodcost = Constants.prodcost * self.player.numsold
        return {
            "prices": zip(range(1, self.subsession.dims + 1),
                             [pd.value for pd in self.group.get_player_by_role("S1").get_ask().pricedim_set.all() ],
                             [pd.value for pd in self.group.get_player_by_role("S2").get_ask().pricedim_set.all()] ),
            "s1_ask_total": self.group.get_player_by_role("S1").ask_total,
            "s2_ask_total": self.group.get_player_by_role("S2").ask_total,
            "b1_seller": self.group.get_player_by_role("B1").contract_seller_rolenum,
            "b2_seller": self.group.get_player_by_role("B2").contract_seller_rolenum,
            "subtotal": self.player.ask_total - Constants.prodcost if self.player.ask_total != None else 0,
            "prodcost": prodcost,
            "benefit": self.player.ask_total * self.player.numsold if self.player.ask_total != None else 0,
        }



# AJAX VIEWS
# Seller Asks
def AutoPricedims(request):

    pricejson = utils.get_autopricedims(
        ask_total=int(round(float(request.POST["ask_total"]))), numdims=int(round(float(request.POST["numdims"]))))

    if not request.POST["example"] == "True":
        # If this is being called from the instructions screen, we skip adding a row
        player = utils.get_player_from_request(request)

        ask = player.create_ask(total=pricejson["ask_total"], auto=True, manual=False, stdev=pricejson["ask_stdev"],
                            pricedims=pricejson["pricedims"])

    return JsonResponse(pricejson)

def ManualPricedims(request):

    result = request.POST.dict()

    pricedims_raw = result["pricedims"].split(",")
    pricedims = [None if pd=="" else int(round(float(pd))) for pd in pricedims_raw]
    total = sum([0 if pd=="" else int(round(float(pd))) for pd in pricedims_raw])

    if not request.POST["example"] == "True":
        # If this is being called from the instructions screen, we skip adding a row
        player = utils.get_player_from_request(request)

        ask = player.create_ask(total=total, auto=False, manual=True, pricedims=pricedims)
        ask.stdev = pstdev([int(pd.value) for pd in ask.pricedim_set.all() if not pd.value==None ])
        ask.save()

        return JsonResponse({"pricedims": pricedims, "ask_total": ask.total, "ask_stdev": ask.stdev})
    else:
        # If here, this is an example request from the instructions screen
        return JsonResponse({"pricedims": pricedims, "ask_total": total, "ask_stdev": 0})



# Wait Page Game
def GameWaitIterCorrect(request):

    player = utils.get_player_from_request(request)
    player.gamewait_numcorrect += 1
    player.save()

    return JsonResponse({"gamewait_numcorrect": player.gamewait_numcorrect})



# Data Views
@login_required
def ViewData(request):
    return render(request, 'duopoly_rep_treat/adminData.html', {"session_code": Session.objects.last().code})

@login_required
def AskDataView(request):
    (headers, body) = export.export_asks()

    context = {"title": "Seller Ask Data", "headers": headers, "body": body}
    return render(request, 'duopoly_rep_treat/AdminDataView.html', context)

@login_required
def AskDataDownload(request):

    headers, body = export.export_asks()
    return export.export_csv("AskData", headers, body)

@login_required
def ContractDataView(request):
    (headers, body) = export.export_contracts()

    context = {"title": "Contracts Data", "headers": headers, "body": body}
    return render(request, 'duopoly_rep_treat/AdminDataView.html', context)

@login_required
def ContractDataDownload(request):
    headers, body = export.export_contracts()
    return export.export_csv("ContractData", headers, body)

@login_required
def MarketDataView(request):
    headers, body = export.export_marketdata()
    context = {"title": "Market Data", "headers": headers, "body": body}

    return render(request, 'duopoly_rep_treat/AdminDataView.html', context)

@login_required
def MarketDataDownload(request):

    headers, body = export.export_marketdata()
    return export.export_csv("MarketData", headers, body)

@login_required
def SurveyDataView(request):
    headers, body = export.export_surveydata()
    context = {"title": "Survey Data", "headers": headers, "body": body}

    return render(request, 'duopoly_rep_treat/AdminDataView.html', context)

@login_required
def SurveyDataDownload(request):

    headers, body = export.export_surveydata()
    return export.export_csv("SurveyData", headers, body)

@login_required
def CombinedDataView(request):
    headers, body = export.export_combineddata()
    context = {"title": "Combined Data", "headers": headers, "body": body}

    return render(request, 'duopoly_rep_treat/AdminDataView.html', context)

@login_required
def CombinedDataDownload(request):

    headers, body = export.export_combineddata()
    return export.export_csv("CombinedData", headers, body)

def CodebookDownload(request, app_label):

    headers, body = export.export_docs(app_label)
    return export.export_csv("Codebook", headers, body)


page_sequence = [
    WaitStartInstructions,
    IntroductionSplash,
    IntroductionPRA,
    InstructionsBasics,
    InstructionsBasicsQuiz,
    InstructionsRoles,
    InstructionsRolesQuiz,
    InstructionsNewTreatment,
    InstructionsSeller,
    InstructionsSellerQuiz,
    InstructionsBuyer,
    InstructionsBuyerQuiz,
    InstructionsRoundResults,
    InstructionsWaitGame,
    WaitStartMatch,
    PracticeBegin,
    PracticeEnd,
    ChoiceSeller,
    WaitSellersForSellers,  # for buyers while they wait for sellers # split in tow
    WaitBuyersForSellers,  # for buyers while they wait for sellers # split in tow
    ChoiceBuyer,
    WaitGame, # both buyers and sellers go here while waiting for buyers
    WaitRoundResults,
    RoundResults
]
