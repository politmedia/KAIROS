from core import models
from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import translator


class PartyTranslationOptions(TranslationOptions):
    fields = ('name', 'shortname',)


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


class QuestionTranslationOptions(TranslationOptions):
    fields = ('text', 'description',)


class ConstituencyTranslationOptions(TranslationOptions):
    fields = ('name',)


translator.register(models.Party, PartyTranslationOptions)
translator.register(models.Category, CategoryTranslationOptions)
translator.register(models.Question, QuestionTranslationOptions)
translator.register(models.Constituency, ConstituencyTranslationOptions)
