from easy_thumbnails.files import get_thumbnailer


class UserProfileSerializer:

    @classmethod
    def serialize(cls, objects):
        output = []
        for obj in objects:
            image = obj.user.picture or 'default_profile.png'
            output.append({
                'name': obj.user.get_full_name(),
                'url': obj.get_permalink(),
                'team': obj.display_team,
                'league': obj.display_league,
                'image':  get_thumbnailer(image)['nav_avatar'].url
            })
        return output


class PlayerProfileSerializer(UserProfileSerializer):
    pass


class CoachProfileSerializer(UserProfileSerializer):
    pass
