import os
from collections import defaultdict

import logging
import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup

from .converters import PHPClassConverter
from .objects import *

log = logging.getLogger("docs_parser.run")


def download() -> str:
    log.debug("running docs download")
    log.info("downloading APIs landing page")
    s = requests.Session()
    s.mount("https://", HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=3))

    r = s.get("https://developer.riotgames.com/apis")
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html5lib")

    apis = []
    apis_errored = []
    api_data = ""
    for api_option in soup.select("a.api_option"):
        api_option_name = api_option["api-name"]
        api_option_link = f"https://developer.riotgames.com/api-details/{api_option_name}"

        try:
            log.debug("downloading API details for %s from %s", api_option_name, api_option_link)
            r = s.get(api_option_link)
            r.raise_for_status()
            api_option_data = r.json()

            apis.append(api_option_name)
            api_data += api_option_data["html"]

        except Exception as ex:
            apis_errored.append(api_option_name)
            log.exception("download and processing of API details for %s failed!", api_option_name)

    log.info("successfully downloaded API details of %s", apis)
    if apis_errored:
        log.warning("some API details failed to be downloaded: %s", apis_errored)

    output_filepath = "input/input.html"
    log.debug("writing downloaded API details to '%s'", output_filepath)
    with open(output_filepath, "wb") as fd:
        fd.write(api_data.encode("utf-8"))

    s.close()
    return api_data


def parse(content: str = None) -> tuple[list[Resource], list[ObjectDefinition]]:
    log.debug("running docs parsing")
    if not content:
        input_filename = "input/input.html"
        log.debug("loading docs sources from %s", input_filename)
        with open(input_filename, "r") as f:
            content = f.readlines()
        content = "".join([str(line) for line in content])

    soup = BeautifulSoup(content, "html5lib")
    objects: dict[str, ObjectDefinition] = dict()
    resources: list[Resource] = list()
    for resource_data in soup.select(".resource"):
        log.debug("processing new resource definition")

        resource_link = resource_data.find("a")["href"]
        _, resource_id = resource_data["id"].rsplit("_")
        resource_name, resource_version = resource_data["api-name"].rsplit("-", maxsplit=1)

        resource = Resource(
            id=int(resource_id),
            name=resource_name,
            version=resource_version,
            api_link=resource_link,
            operations=[],
        )
        resources.append(resource)
        log.info("processing %s resource", resource.as_source)

        for operation_data in resource_data.select(".operation"):
            log.debug("processing new operation definition")

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
            log.info("processing operation %s.%s", resource.name, operation.id)

            for object_data in operation_data.select(".response_body"):
                log.debug("processing new response body definition")

                if "Return value:" in object_data.text:
                    _, return_type = object_data.text.split(":")
                    operation.returns = return_type.strip()
                    log.info("designated operation return type: %s", operation.returns)
                    continue

                elif (object_heading := object_data.select_one("h5")) is None:
                    if (object_heading := object_data.select_one("div > b")) is None:
                        log.warning("skipping definition: %s", object_data)
                        continue

                object_name = object_heading.text.strip()
                if object_name in objects:
                    obj = objects[object_name]
                    log.debug("reusing definition of object %s", obj.name)

                else:
                    obj = ObjectDefinition(
                        name=object_name,
                        description="",
                        properties=dict(),
                        sources=defaultdict(set),
                    )
                    objects[obj.name] = obj
                    log.info("created new definition of object %s", obj.name)

                obj.sources[resource].add(operation)
                log.debug("adding new source to object definition, resource=%s, operation=%s",
                          resource.as_source, operation.id)

                for prop_entry in object_data.select("table > tbody tr"):
                    prop_name, prop_type, prop_desc = prop_entry.select("td")
                    prop_name = prop_name.text.strip()
                    if prop_name in obj.properties:
                        prop = obj.properties[prop_name]
                        log.debug("reusing definition of object property %s", prop.name)

                    else:
                        prop = ObjectProperty(
                            name=prop_name,
                            type=prop_type.text.strip(),
                            description=prop_desc.text.strip(),
                            sources=defaultdict(set),
                        )
                        obj.properties[prop.name] = prop
                        log.info("created new definition of object property %s", prop.name)

                    prop.sources[resource].add(operation)
                    log.debug("adding new source to object property definition, resource=%s, operation=%s",
                              resource.as_source, operation.id)

    object_list = list(objects.values())
    log.info("located %d resources and parsed %d objects", len(resources), len(object_list))
    return resources, object_list


def generate(resources: list[Resource], objects: list[ObjectDefinition]):
    log.debug("running docs conversion")
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

    for obj in objects:
        packages = converter.packages(obj)
        for package, op in packages:
            dirpath = converter.dirname(op)
            os.makedirs(dirpath, exist_ok=True)
            filepath = f"{dirpath}/{converter.filename(obj)}"
            log.debug("writing definition of object %s to %s", obj.name, filepath)
            with open(filepath, "wb") as fd:
                fd.write(converter.contents(obj, op).lstrip().encode("utf-8"))


def run(run_download: bool):
    content = None
    if run_download:
        content = download()

    resources, objects = parse(content)
    generate(resources, objects)
    log.info("finished!")
