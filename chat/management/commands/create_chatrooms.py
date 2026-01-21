from django.core.management.base import BaseCommand
from match.models import MatchRequest
from chat.models import ChatRoom

class Command(BaseCommand):
    help = "Create chat rooms for all accepted match requests that don't have one"

    def handle(self, *args, **kwargs):
        accepted_requests = MatchRequest.objects.filter(
            status="accepted"
        ).exclude(chat_room__isnull=False)

        created_count = 0

        for req in accepted_requests:
            # Sort users to avoid unique_together conflict
            user1, user2 = sorted([req.from_user, req.to_user], key=lambda u: u.id)

            chat_room, created = ChatRoom.objects.get_or_create(
                user1=user1,
                user2=user2,
                defaults={"match_request": req}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Chat room created: {chat_room.id} for {user1.email} & {user2.email}"
                    )
                )
            else:
                self.stdout.write(
                    f"Chat room already exists for {user1.email} & {user2.email}"
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Total new chat rooms created: {created_count}"))
