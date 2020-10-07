from django.db.models import Q

import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError

from users.schema import UserType

from .models import Link, Vote
from .paginator_helper import get_paginator

class LinkType(DjangoObjectType):
    class Meta:
        model = Link


class VoteType(DjangoObjectType):
    class Meta:
        model = Vote

# Now we create a corresponding PaginatedType for that object type:
class LinkPaginatedType(graphene.ObjectType):
    page = graphene.Int()
    pages = graphene.Int()
    total_record = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()
    objects = graphene.List(LinkType)

class Query(graphene.ObjectType):
    links = graphene.Field(LinkPaginatedType, offset=graphene.Int(), limit = graphene.Int())
    # links = graphene.Field(LinkPaginatedType, page=graphene.Int())

    # links = graphene.List(
    #     LinkType,
    #     search=graphene.String(),
    #     first=graphene.Int(),
    #     skip=graphene.Int(),
    # )
    votes = graphene.List(VoteType)

    def resolve_links(self, info, offset, limit):
        print("offset",offset)
        print("limit",limit)        
        # page_size = limit
        # page = offset
        qs = Link.objects.all()
        return get_paginator(qs, limit, offset, LinkPaginatedType)

    # def resolve_links(self, info, search=None, first=None, skip=None, **kwargs):
    #     qs = Link.objects.all()

    #     if search:
    #         filter = (
    #             Q(url__icontains=search) |
    #             Q(description__icontains=search)
    #         )
    #         qs = qs.filter(filter)

    #     if skip:
    #         qs = qs[skip::]

    #     if first:
    #         qs = qs[:first]

    #     return qs

    def resolve_votes(self, info, **kwargs):
        return Vote.objects.all()


class CreateLink(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        url = graphene.String()
        description = graphene.String()

    def mutate(self, info, url, description):
        user = info.context.user
        link = Link(
            url=url,
            description=description,
            posted_by=user,
        )
        link.save()

        return CreateLink(
            id=link.id,
            url=link.url,
            description=link.description,
            posted_by=link.posted_by,
        )


class CreateVote(graphene.Mutation):
    user = graphene.Field(UserType)
    link = graphene.Field(LinkType)

    class Arguments:
        link_id = graphene.Int()

    def mutate(self, info, link_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged in to vote!')

        link = Link.objects.filter(id=link_id).first()
        if not link:
            raise Exception('Invalid Link!')

        Vote.objects.create(
            user=user,
            link=link,
        )

        return CreateVote(user=user, link=link)


class Mutation(graphene.ObjectType):
    create_link = CreateLink.Field()
    create_vote = CreateVote.Field()
