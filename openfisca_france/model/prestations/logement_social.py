# -*- coding: utf-8 -*-

from openfisca_france.model.base import *  # noqa analysis:ignore

import logging
from pprint import pformat
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Paris, Aubervilliers, Bagnolet, Boulogne-Billancourt, Charenton-le-Pont, Clichy-la-Garenne, Fontenay-sous-Bois,
# Gentilly, Issy-les-Moulineaux, Ivry-sur-Seine, Joinville-le-Pont, le Kremlin-Bicêtre, Les Lilas, Le Pré-Saint-Gervais,
# Levallois-Perret, Malakoff, Montreuil, Montrouge, Neuilly-sur-Seine, Nogent-sur-Marne, Pantin, Puteaux, Saint-Cloud,
# Saint-Denis, Saint-Mandé, Saint-Maurice, Saint-Ouen, Suresnes, Vanves, Vincennes
paris_communes_limitrophes = [
    '75100',
    '93001',
    '93006',
    '94018',
    '92024',
    '94033',
    '94037',
    '92040',
    '94041',
    '94042',
    '94043',
    '93045',
    '93061',
    '92044',
    '92046',
    '93048',
    '92049',
    '92051',
    '94052',
    '93055',
    '92062',
    '92064',
    '93066',
    '94067',
    '94069',
    '93070',
    '92073',
    '92075',
    '94080'
]

class ZoneLogementSocial(Enum):
    __order__ = 'paris_communes_limitrophes ile_de_france autres_regions'
    paris_communes_limitrophes = u"Paris et communes limitrophes"
    ile_de_france = u"Île-de-France hors Paris et communes limitrophes"
    autres_regions = u"Autres régions"


class zone_logement_social(Variable):
    value_type = Enum
    possible_values = ZoneLogementSocial
    default_value = ZoneLogementSocial.autres_regions
    entity = Menage
    definition_period = MONTH
    label = u"Zone logement social"
    def formula(menage, period):

        depcom = menage('depcom', period)
        departement = depcom.astype(int) / 1000

        departements_idf = [75, 77, 78, 91, 92, 93, 94, 95]
        in_idf = sum([departement == departement_idf for departement_idf in departements_idf])

        return select(
            [
                depcom in paris_communes_limitrophes,
                in_idf
            ],
            [
                ZoneLogementSocial.paris_communes_limitrophes,
                ZoneLogementSocial.ile_de_france,
            ],
            default = ZoneLogementSocial.autres_regions
        )

class CategorieMenageLogementSocial(Enum):
    __order__ = 'categorie_1 categorie_2 categorie_3 categorie_4 categorie_5 categorie_6'
    categorie_1 = u"Une personne seule"
    categorie_2 = u"Deux personnes ne comportant aucune pers. à charge à l'exclusion des jeunes ménages"
    categorie_3 = u"Trois personnes ou une pers. seule avec une pers. à charge ou jeune ménage sans personne à charge"
    categorie_4 = u"Quatre personnes ou une pers. seule avec deux pers. à charge"
    categorie_5 = u"Cinq personnes ou une pers. seule avec trois pers. à charge"
    categorie_6 = u"Six personnes ou une pers. seule avec quatre pers. à charge"

class logement_social_categorie_menage(Variable):
    entity = Famille
    value_type = Enum
    possible_values = CategorieMenageLogementSocial
    default_value = CategorieMenageLogementSocial.categorie_1
    definition_period = MONTH
    label = u"Catégorie de ménage pour déterminer le plafond de ressources"
    reference = [
        u"Arrêté du 29 juillet 1987 relatif aux plafonds de ressources des bénéficiaires de la législation sur les habitations à loyer modéré et des nouvelles aides de l'Etat en secteur locatif",
        u"https://www.legifrance.gouv.fr/affichTexte.do?cidTexte=JORFTEXT000000294318"
    ]
    def formula(famille, period, parameters):

        is_couple = famille('al_couple', period)
        personnes_a_charge = famille('al_nb_personnes_a_charge', period)

        # Le couple dont la somme des âges révolus des deux conjoints le composant
        # est au plus égale à cinquante-cinq ans constitue un jeune ménage
        # au sens du présent arrêté.
        age = famille.members('age', period)
        sum_age = famille.sum(age)
        is_jeune_menage = sum_age <= 55

        return select(
            [
                not is_couple and personnes_a_charge == 0,
                is_couple and not is_jeune_menage and personnes_a_charge == 0,
                (is_couple and personnes_a_charge == 1) or (not is_couple and personnes_a_charge == 1) or (is_jeune_menage and personnes_a_charge == 0),
                (is_couple and personnes_a_charge == 2) or (not is_couple and personnes_a_charge == 2),
                (is_couple and personnes_a_charge == 3) or (not is_couple and personnes_a_charge == 3),
                (is_couple and personnes_a_charge == 4) or (not is_couple and personnes_a_charge == 4),
            ],
            [
                CategorieMenageLogementSocial.categorie_1,
                CategorieMenageLogementSocial.categorie_2,
                CategorieMenageLogementSocial.categorie_3,
                CategorieMenageLogementSocial.categorie_4,
                CategorieMenageLogementSocial.categorie_5,
                CategorieMenageLogementSocial.categorie_6,
            ],
            default = CategorieMenageLogementSocial.categorie_1
        )

class logement_social_plafond_ressources(Variable):
    entity = Famille
    value_type = float
    definition_period = MONTH
    label = u"Plafonds de ressources des bénéficiaires de la législation sur les habitations à loyer modéré et des nouvelles aides de l'Etat en secteur locatif"
    reference = [
        u"Arrêté du 22 décembre 2016 modifiant l'arrêté du 29 juillet 1987 relatif aux plafonds de ressources des bénéficiaires de la législation sur les habitations à loyer modéré et des nouvelles aides de l'Etat en secteur locatif ",
        u"https://www.legifrance.gouv.fr/affichTexte.do;jsessionid=186AC8F0B7590C42DAA390BA6C89612B.tpdila11v_1?cidTexte=JORFTEXT000033681769&dateTexte=&oldAction=rechJO&categorieLien=id&idJO=JORFCONT000033680662",
    ]

    def formula(famille, period, parameters):

        logement_social = parameters(period).prestations.logement_social

        categorie_menage = famille('logement_social_categorie_menage', period)
        zone_logement_social = famille.demandeur.menage('zone_logement_social', period)

        plafond_ressources_par_categorie = logement_social.plafond_ressources.par_categorie_de_menage[categorie_menage]

        try:
            plafond_ressources = plafond_ressources_par_categorie[zone_logement_social]
        except ValueError:
            plafond_ressources = plafond_ressources_par_categorie['autres_regions']

        return plafond_ressources

class logement_social_eligible(Variable):
    entity = Famille
    value_type = bool
    definition_period = MONTH
    label = u"Logement social - Éligibilité"

    def formula(famille, period, parameters):

        logement_social_plafond_ressources = famille('logement_social_plafond_ressources', period)
        revenu_fiscal_de_reference = famille.demandeur.foyer_fiscal('rfr', period.n_2)

        return revenu_fiscal_de_reference <= logement_social_plafond_ressources
