import os
from collections import defaultdict

from bs4 import BeautifulSoup

from .converters import PHPClassConverter
from .objects import *


def run(content: str):
    soup = BeautifulSoup(content, "html5lib")
    objects: dict[str, ObjectDefinition] = dict()
    resources: list[Resource] = list()
    for resource_data in soup.select(".resource"):
        link = resource_data.find("a")["href"]
        _, resource_id = resource_data["id"].rsplit("_")
        name, version = resource_data["api-name"].rsplit("-", maxsplit=1)

        resource = Resource(
            id=int(resource_id),
            name=name,
            version=version,
            api_link=link,
            operations=[],
        )
        resources.append(resource)

        for operation_data in resource_data.select(".operation"):
            operation_link = operation_data.find("a")["href"]
            operation_method, operation_id = operation_link.rsplit("/", maxsplit=1)[1].split("_")
            operation_path = operation_data.select_one("span.path").text.strip()

            operation = Operation(
                id=operation_id,
                method=operation_method,
                returns="_unknown_",
                docs_link=operation_link,
                api_path=operation_path,
            )
            resource.operations.append(operation)

            for object_data in operation_data.select(".response_body"):
                if "Return value:" in object_data.text:
                    _, return_type = object_data.text.split(":")
                    operation.returns = return_type.strip()
                    continue

                elif (object_heading := object_data.select_one("h5")) is None:
                    continue

                object_name = object_heading.text.strip()
                if object_name in objects:
                    obj = objects[object_name]

                else:
                    obj = ObjectDefinition(
                        name=object_name,
                        description="",
                        properties=dict(),
                        sources=defaultdict(set),
                    )
                    objects[obj.name] = obj

                obj.sources[resource].add(operation)

                for prop_entry in object_data.select("table > tbody tr"):
                    prop_name, prop_type, prop_desc = prop_entry.select("td")
                    prop_name = prop_name.text.strip()
                    if prop_name in obj.properties:
                        prop = obj.properties[prop_name]

                    else:
                        prop = ObjectProperty(
                            name=prop_name,
                            type=prop_type.text.strip(),
                            description=prop_desc.text.strip(),
                            sources=defaultdict(set),
                        )
                        obj.properties[prop.name] = prop

                    prop.sources[resource].add(operation)

    converter = PHPClassConverter(resources)
    converter.output_dir = "output"
    converter.iterable_classes = {
        "ChampionListDto": "champions",
        "CurrentGameInfo": "participants",
        "FeaturedGames": "gameList",
        "FeaturedGameInfo": "participants",
        "Incident": "updates",
        "LeagueListDto": "entries",
        "LobbyEventDtoWrapper": "eventList",
        "MasteryPageDto": "masteries",
        "MasteryPagesDto": "pages",
        "MatchlistDto": "matches",
        "MatchTimelineDto": "frames",
        "Message": "translations",
        "Perks": "perkIds",
        "PlayerStatsSummaryListDto": "playerStatSummaries",
        "RankedStatsDto": "champions",
        "RecentGamesDto": "games",
        "RunePageDto": "slots",
        "RunePagesDto": "pages",
        "Service": "incidents",
        "ShardStatus": "services",
        "Timeline": "frames",
    }
    converter.linkable_classes = {
        "BannedChampion": ("getStaticChampion", "championId"),
        "ChampionDto": ("getStaticChampion", "id"),
        "ChampionMasteryDto": ("getStaticChampion", "championId"),
        "CurrentGameParticipant": ("getStaticChampion", "championId"),
        "MatchReferenceDto": ("getStaticChampion", "champion"),
        "Participant": ("getStaticChampion", "championId"),
        "ParticipantDto": ("getStaticChampion", "championId"),
        "TeamBansDto": ("getStaticChampion", "championId"),
    }

    for obj in objects.values():
        dirpath = converter.dirname(obj)
        os.makedirs(dirpath, exist_ok=True)
        filepath = f"{dirpath}/{converter.filename(obj)}"
        print(filepath)
        with open(filepath, "wb") as fd:
            fd.write(converter.contents(obj).lstrip().encode("utf-8"))
