import datetime
import logging
import re
from itertools import chain

from .base import ConverterBase
from ..objects import ObjectDefinition, Resource, ObjectProperty

log = logging.getLogger("php_class_converter")


class PHPClassConverter(ConverterBase):

    standard_data_types = ["integer", "string", "bool", "float", "array"]

    def __init__(self, resources: list[Resource]):
        super().__init__(resources)

        self.output_dir: str = ""
        self.iterable_classes: dict[str, str] = {}
        self.linkable_classes: dict[str, tuple[str, str]] = {}

    def _get_package_name(self, obj: ObjectDefinition) -> str:
        api_path_bases = {o.api_path[:o.api_path[1:].find("/") + 1] for o in chain(*obj.sources.values())}
        if len(api_path_bases) > 1:
            log.warning("class has more than one API path bases")

        api_path_base = api_path_bases.pop()
        if api_path_base == "/lol":
            api_class = "LeagueAPI"

        elif api_path_base == "/lor":
            api_class = "RuneterraAPI"

        elif api_path_base == "/val":
            api_class = "ValorantAPI"

        elif api_path_base == "/tft":
            api_class = "TFTAPI"

        elif api_path_base == "/riot":
            api_class = "RiotAPI"

        else:
            api_class = "_UNKNOWN_"

        return f"RiotAPI\\{api_class}\\Objects"

    def _get_uses(self, obj: ObjectDefinition) -> str:
        return ""

    def _get_class_name(self, obj: ObjectDefinition) -> str:
        name = obj.name
        name = name.replace("DTO", "Dto")

        return name

    def _get_class_annotation(self, obj: ObjectDefinition) -> str:
        annotation_lines = []

        if obj.description:
            annotation_lines.extend([
                "",
                obj.description,
            ])

        annotation_lines.extend([
            "",
            *self._get_class_used_by(obj),
        ])

        if obj.name in self.linkable_classes:
            link_method, link_prop = self.linkable_classes[obj.name]
            annotation_lines.extend([
                "",
                f" @linkable {link_method}(${link_prop})"
            ])

        elif obj.name in self.iterable_classes:
            iter_prop = self.iterable_classes[obj.name]
            annotation_lines.extend([
                "",
                f" @iterable ${iter_prop}"
            ])

        return "\n *".join(annotation_lines)

    def _get_class_extends(self, obj: ObjectDefinition) -> str:
        if obj.name in self.linkable_classes:
            return " extends ApiObjectLinkable"

        elif obj.name in self.iterable_classes:
            return " extends ApiObjectIterable"

        return " extends ApiObject"

    def _get_class_property_description(self, prop: ObjectProperty) -> list[str]:
        description = []
        if len(prop.description):
            if not prop.description.endswith("."):
                prop.description += "."

            desc_line = []
            char_count = 8
            desc_split = prop.description.split()
            for _id, word in enumerate(desc_split):
                char_count += len(word) + 1
                if char_count > 80:
                    description.append(" * " + " ".join(desc_line))
                    desc_line = [word]

                    char_count = 8 + len(word) + 1

                else:
                    desc_line.append(word)

            if desc_line:
                description.append(" * " + " ".join(desc_line))

        return description

    def _get_class_used_by(self, obj: ObjectDefinition) -> list[str]:
        lines = [" Used in:"]
        _, class_name, _ = self._get_package_name(obj).split("\\")

        for resource, operations in obj.sources.items():
            lines.append(f"   {resource.as_source}")
            for operation in operations:
                lines.extend([
                    f"     - @see {class_name}::{operation.id}",
                    f"       @link {operation.docs_link}",
                ])

        return lines

    def _get_class_property_used_by(self, prop: ObjectProperty, obj: ObjectDefinition) -> list[str]:
        lines = [" * Available when received from:"]
        _, class_name, _ = self._get_package_name(obj).split("\\")

        for resource, operations in prop.sources.items():
            for operation in operations:
                lines.append(f" *   - @see {class_name}::{operation.id}")

        return lines

    def _get_class_property_type(self, prop: ObjectProperty) -> str:
        if match := re.match(r"^.*\[(.+)]$", prop.type):
            return f"{self._get_php_datatype(match.group(1))}[]"

        return self._get_php_datatype(prop.type)

    def _get_php_datatype(self, type_name: str) -> str:
        if type_name.lower() in ["float", "double"]:
            return "float"

        if type_name.lower() in ["int", "long"]:
            return "int"

        if type_name.lower() in ["bool", "boolean"]:
            return "bool"

        return type_name

    def _get_class_properties(self, obj: ObjectDefinition) -> str:
        prop_strings = []

        for prop in obj.properties.values():
            description = self._get_class_property_description(prop)
            used_by = self._get_class_property_used_by(prop, obj)

            prop_strings.append("/**")
            if description:
                prop_strings.extend([
                    *description,
                    " *",
                ])

            prop_strings.extend([
                *used_by,
                " *",
                f" * @var {self._get_class_property_type(prop)} ${prop.name}",
                " */",
            ])

            prop_strings.append(f"public ${prop.name};\n")

        return "\n\t" + "\n\t".join(prop_strings)

    def dirname(self, obj: ObjectDefinition) -> str:
        _, name, _ = self._get_package_name(obj).split("\\")
        return f"{self.output_dir}/{name}"

    def filename(self, obj: ObjectDefinition) -> str:
        return f"{self._get_class_name(obj)}.php"

    def contents(self, obj: ObjectDefinition) -> str:
        return f'''
<?php

/**
 * Copyright (C) 2016-{datetime.datetime.now().year}  Daniel Dolejška
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

namespace {self._get_package_name(obj)};
{self._get_uses(obj)}

/**
 *   Class {self._get_class_name(obj)}
 *{self._get_class_annotation(obj)}
 *
 * @package {self._get_package_name(obj)}
 */
class {self._get_class_name(obj)}{self._get_class_extends(obj)}
''' + "{" + self._get_class_properties(obj) + "}\n"

