from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "unraid" / "my-RTFM.xml"
README = ROOT / "README.md"
GUIDE = ROOT / "docs" / "UNRAID-INSTALLATION.md"

SECRETS = {
    "APP_TOKEN": "app-token",
    "SESSION_SECRET": "session-secret",
    "REPLICATION_TOKEN": "replication-token",
    "KEEPALIVED_API_KEY": "keepalived-api-key",
}
HOST_ROOT = "/mnt/user/appdata/rtfm/secrets"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def config_by_target(root: ET.Element) -> dict[str, ET.Element]:
    result: dict[str, ET.Element] = {}
    for config in root.findall("Config"):
        target = config.get("Target", "")
        require(target, "Todos los Config deben declarar Target")
        require(target not in result, f"Target duplicado en plantilla: {target}")
        result[target] = config
    return result


def validate_template() -> None:
    raw = TEMPLATE.read_text(encoding="utf-8")
    root = ET.fromstring(raw)
    require(root.tag == "Container", "La raiz XML debe ser Container")
    configs = config_by_target(root)

    expected_mounts: set[str] = set()
    expected_file_variables: set[str] = set()
    for direct_name, filename in SECRETS.items():
        internal = f"/run/secrets/{filename}"
        host = f"{HOST_ROOT}/{filename}"
        file_variable = f"{direct_name}_FILE"
        expected_mounts.add(internal)
        expected_file_variables.add(file_variable)

        require(direct_name not in configs, f"La plantilla no debe pasar {direct_name} directamente")

        mount = configs.get(internal)
        require(mount is not None, f"Falta el mount de {direct_name}: {internal}")
        require(mount.get("Type") == "Path", f"{internal} debe ser Type=Path")
        require(mount.get("Mode") == "ro", f"{internal} debe montarse en modo ro")
        require(mount.get("Required") == "true", f"{internal} debe exigir un fichero host")
        require(mount.get("Mask") == "false", f"La ruta host de {direct_name} no es un secreto")
        require(mount.get("Default") == host, f"Ruta host no generica para {direct_name}")
        require((mount.text or "").strip() == host, f"Valor host inesperado para {direct_name}")
        description = mount.get("Description", "")
        require("0400" in description, f"Falta modo 0400 en la descripcion de {direct_name}")
        require("10001:10001" in description, f"Falta propietario 10001:10001 para {direct_name}")

        file_config = configs.get(file_variable)
        require(file_config is not None, f"Falta {file_variable}")
        require(file_config.get("Type") == "Variable", f"{file_variable} debe ser Variable")
        require(file_config.get("Required") == "true", f"{file_variable} debe ser obligatorio")
        require(file_config.get("Mask") == "false", f"{file_variable} solo contiene una ruta")
        require(file_config.get("Default") == internal, f"Default incorrecto en {file_variable}")
        require((file_config.text or "").strip() == internal, f"Valor incorrecto en {file_variable}")

    actual_mounts = {
        target
        for target, config in configs.items()
        if target.startswith("/run/secrets/") and config.get("Type") == "Path"
    }
    actual_file_variables = {
        target
        for target in configs
        if target in {f"{name}_FILE" for name in SECRETS}
    }
    require(actual_mounts == expected_mounts, "El conjunto de mounts secretos no es exacto")
    require(
        actual_file_variables == expected_file_variables,
        "El conjunto de variables *_FILE no es exacto",
    )

    require(
        not re.search(r"(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)", raw),
        "La plantilla contiene una IP privada incrustada",
    )
    require("__" not in raw, "La plantilla contiene un marcador sin resolver")
    require(
        "--read-only" in root.findtext("ExtraParams", default=""),
        "El filesystem del contenedor debe permanecer read-only",
    )
    forwarded = configs.get("FORWARDED_ALLOW_IPS")
    require(forwarded is not None, "Falta FORWARDED_ALLOW_IPS en la plantilla")
    require(
        forwarded.get("Default") == "127.0.0.1"
        and (forwarded.text or "").strip() == "127.0.0.1",
        "FORWARDED_ALLOW_IPS debe fallar cerrado a loopback",
    )
    require(
        forwarded.get("Default") != "*" and (forwarded.text or "").strip() != "*",
        "La plantilla no debe confiar en cualquier proxy",
    )


def validate_documentation() -> None:
    readme = README.read_text(encoding="utf-8")
    guide = GUIDE.read_text(encoding="utf-8")

    readme_requirements = (
        "docs/UNRAID-INSTALLATION.md",
        "10001:10001",
        "modo `0400`",
        "no aparecen en",
        "`docker inspect`",
        "usa exclusivamente sus equivalentes `*_FILE`",
    )
    for fragment in readme_requirements:
        require(fragment in readme, f"README no documenta: {fragment}")

    guide_requirements = (
        "install -d -o 10001 -g 10001 -m 0700",
        "install -o 10001 -g 10001 -m 0400",
        "APP_TOKEN_FILE=/run/secrets/app-token",
        "SESSION_SECRET_FILE=/run/secrets/session-secret",
        "REPLICATION_TOKEN_FILE=/run/secrets/replication-token",
        "KEEPALIVED_API_KEY_FILE=/run/secrets/keepalived-api-key",
        "docker inspect RTFM",
        "rw=false",
        "APP_TOKEN retirado",
        "Migración desde variables directas",
        "no incluye campos directos ni secretos predeterminados",
        "FORWARDED_ALLOW_IPS=127.0.0.1",
        "Nunca uses `*`",
    )
    for fragment in guide_requirements:
        require(fragment in guide, f"La guia Unraid no documenta: {fragment}")


def main() -> int:
    try:
        validate_template()
        validate_documentation()
    except (AssertionError, ET.ParseError, OSError) as error:
        print(f"unraid-template: ERROR: {error}", file=sys.stderr)
        return 1
    print("unraid-template: XML, secretos por fichero y documentacion OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
