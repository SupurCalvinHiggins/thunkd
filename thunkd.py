"""
Thunkable Download Tool

thunkd.py
Core logic to download projects from Thunkable.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
disclaimer.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import re
import copy
import json
import shutil
import logging
import argparse
import requests
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.resolve().joinpath("thunkd_py_config.json")


def dump_json(data: dict) -> str:
    """
    Convert a dictionary to a formatted JSON string.

    Parameters
    ----------
    data: The dictionary.

    Returns
    -------
    The formatted JSON string.
    """
    return json.dumps(data, indent=4)


def dump_xml(data: str) -> str:
    """
    Convert a XML string to a formatted XML string. Right now, this does not apply any formatting. This is because the
    XML parsers I tried produced formatted output strings that were no longer compatible with the Thunkable backend.
    However, if you can find a way to robustly format the XML that works with Thunkable, just update this function and
    the formatting will be applied to the downloaded XML files.

    Parameters
    ----------
    data: The XML string.

    Returns
    -------
    The formatted XML string.
    """
    return data


def load_json(data: str) -> dict:
    """
    Convert a formatted JSON string to a dictionary.

    Parameters
    ----------
    data: The formatted JSON string.

    Returns
    -------
    The dictionary.
    """
    return json.loads(data)


def load_xml(data: str) -> str:
    """
    Convert a formatted XML string to a XML string.

    Parameters
    ----------
    data: The formatted XML string.

    Returns
    -------
    The XML string.
    """
    return data
    

def safe_read_config() -> dict:
    """
    Returns the configuration as a dictionary. If the configuration cannot be loaded, an error message is printed
    and the program exits with error code 1.

    Returns
    -------
    The configuration.
    """
    try:
        config = load_json(CONFIG_PATH.read_text())
        if "thunk_token" not in config:
            logging.fatal("The thunk_token is not set. Set the thunk_token")
            exit(1)
        return config
    except OSError:
        logging.fatal("The configuration file does not exist.")
        logging.info("The configuration file might be in the wrong directory.")
        logging.info("The thunk_token might not be set. Set the thunk_token.")
        exit(1)
    except json.JSONDecodeError:
        logging.fatal("The configuration file is not valid JSON.")
        logging.info("The thunk_token might not be set. Set the thunk_token.")
        exit(1)


def read_modular_project(project_path: Path) -> dict:
    """
    Load a modular project from disk. A modular project is a mapping from file names to file content.

    Parameters
    ----------
    project_path: The modular project path.

    Returns
    -------
    The modular project.
    """
    modular_project = {}
    suffix_to_load = {".json": load_json, ".xml": load_xml}
    # Map the name of each file in the project path to its contents as a Python object.
    # TODO: This glob does not always work since directories can contain the '.' character.
    for path in project_path.glob("*.*"):
        if path.suffix not in suffix_to_load:
            logging.info("Invalid file encountered in modular project")
            logging.info(f"\tpath = {path}")
            continue
        load_func = suffix_to_load[path.suffix]
        modular_project[path.name] = load_func(path.read_text())
    return modular_project


def write_modular_project(project_path: Path, modular_project: dict) -> None:
    """
    Write a modular project to disk. A modular project is a mapping from file names to file content.

    Parameters
    ----------
    project_path: The modular project path.
    modular_project: The modular project.

    Returns
    -------
    None
    """
    project_path.mkdir(exist_ok=True)
    suffix_to_dump = {".json": dump_json, ".xml": dump_xml}
    # Write the data mapped to each name to disk.
    for name, data in modular_project.items():
        dump_func = suffix_to_dump[Path(name).suffix]
        project_path.joinpath(name).write_text(dump_func(data))


def to_modular_project(project: dict) -> dict:
    """
    Convert a Thunkable project to a modular project. This maps "meta.json" to metadata,
    "<screen_name>.<screen_id>.json" to the UI elements for that screen and "<screen_name>.<screen_id>.xml" to
    the block code for that screen.

    Parameters
    ----------
    project: The Thunkable project.

    Returns
    -------
    The modular project.
    """

    # Ensure there are no unexpected side effects.
    project = copy.deepcopy(project)

    modular_project = {}

    # The "iproject" is the portion of the Thunkable project that contains the data we are interested in.
    iproject = project["data"]["project"]

    # TODO: This is a bit of a hack.
    # We map the ID of each screen to its name so that we can produce the correct file name when extracting the blocks.
    screen_id_to_name = {}

    screens = []
    for screen_or_nav in iproject["components"]["children"]:
        if "Navigator" in screen_or_nav["type"]:
            screens.extend(screen_or_nav["children"])
        else:
            screens.append(screen_or_nav)
    
    for i, screen in enumerate(screens):
        screen_name, screen_id = screen["name"], screen["id"]
        if re.search(r"[^\w\- ]+", screen_name) is not None:
            logging.fatal("Encountered invalid screen name.")
            logging.fatal(f"\tscreen_name = {screen_name}")
            logging.fatal(f"\tscreen_id = {screen_id}")
            logging.info("The screen name cannot contain special characters besides '-' and '_'.")
            exit(1)
        path = f"{screen['name']}.{screen['id']}.json"
        modular_project[path] = copy.deepcopy(screen)
        screen.clear()
        screen["id"] = screen_id
        screen_id_to_name[screen_id] = screen_name

    # Extract the blocks.
    for screen_id in iproject["blockly"]:
        # Ensure that there are actually blocks to extract.
        if "xml" in iproject["blockly"][screen_id]:
            # If the screen no longer exists, ignore the XML.
            if screen_id not in screen_id_to_name:
                # TODO: Clean the dead JSON.
                continue
            # Add the blocks to the modular project.
            path = f"{screen_id_to_name[screen_id]}.{screen_id}.xml"
            modular_project[path] = iproject["blockly"][screen_id]["xml"]

            # Delete the blocks.
            iproject["blockly"][screen_id]["xml"] = ""

    # Everything that is leftover is metadata.
    modular_project["meta.json"] = project
    return modular_project


def from_modular_project(modular_project: dict) -> dict:
    modular_project = copy.deepcopy(modular_project)
    
    project = modular_project["meta.json"]
    del modular_project["meta.json"]

    iproject = project["data"]["project"]

    screens = []
    for screen_or_nav in iproject["components"]["children"]:
        if "name" in screen_or_nav and "Navigator" in screen_or_nav["type"]:
            screens.extend(screen_or_nav["children"])
        else:
            screens.append(screen_or_nav)

    for name, data in modular_project.items():
        path = Path(name)
        if path.suffix == ".json":
            for screen in screens:
                if screen["id"] == str(path.stem).split(".")[-1]:
                    break
            else:
                logging.fatal("Encountered unexpected JSON file.")
                logging.info(f"\t\tpath = {path}")
                exit(1)
            screen.update(data)
        elif path.suffix == ".xml":
            screen_id = path.stem.split(".")[1]
            iproject["blockly"][screen_id]["xml"] = data
        else:
            logging.fatal("Invalid file type encountered in modular project.")
            logging.info(f"\t\tname = {name}")
            exit(1)
    
    return project


def delete_path_if_exists(d: dict, path: list):
    if len(path) == 0 or not isinstance(d, dict) or path[0] not in d:
        return
    
    if len(path) == 1:
        del d[path[0]]
        return
    
    delete_path_if_exists(d=d[path[0]], path=path[1:])


def to_clean_project(project: dict) -> dict:
    project = copy.deepcopy(project)
    dirty_paths = [
        ["data", "user"],
        ["data", "project", "id"],
        ["data", "project", "blocklyStringLength"],
        ["data", "project", "componentStringLength"],
        ["data", "project", "createdAt"],
        ["data", "project", "email"],
        ["data", "project", "hash"],
        ["data", "project", "isArchiveProjectFileUsed"],
        ["data", "project", "isHiddenFromPublicGallery"],
        ["data", "project", "isLegacy"],
        ["data", "project", "isOwner"],
        ["data", "project", "isPublic"],
        ["data", "project", "isQRCodeScanned"],
        ["data", "project", "isLiveTesting"],
        ["data", "project", "settings", "packageName"],
        ["data", "project", "projectSettings", "packageName"],
        ["data", "project", "storageSize"],
        ["data", "project", "webAppSettings"],
        ["data", "project", "webCompanionSettings"],
        ["data", "project", "frontendProperties"],
        ["data", "project", "appId"],
        ["data", "project", "readOnly"],
        ["data", "project", "shares"],
        ["data", "project", "versions"],
        ["data", "project", "shares"],
        ["data", "project", "projectSnapshotsMetaData"],
        ["data", "project", "projectSnapshotParentId"],
        ["data", "project", "projectSnapshotParent"],
        ["data", "project", "updatedAt"],
        ["data", "project", "username"],
    ]

    iproject = project["data"]["project"]
    for screen_id in iproject["blockly"]:
        for prop in ["code", "appVariableDefCode"]:
            if prop in iproject["blockly"][screen_id]:
                dirty_paths.append(
                    ["data", "project", "blockly", screen_id, prop]
                )

    for path in dirty_paths:
        delete_path_if_exists(d=project, path=path)

    return project


def build_pull_request(project_id: str, config: dict) -> dict:
    return {
        "url": "https://x.thunkable.com/graphql",
        "cookies": {"thunk_token": config["thunk_token"]},
        "json": {
            "operationName": "Project",
            "variables": {
                "id": project_id,
            },
            "query": "query Project($id:ID!,$archiveFilename:String){\n project(id:$id,archiveFilename:$archiveFilename){\n id\n apiComponents\n assets\n backendUpgradeVersion\n blockly\n blocklyStringLength\n categories\n components\n componentStringLength\n createdAt\n figmaComponents\n description\n email\n hash\n icon\n isArchiveProjectFileUsed\n isHiddenFromPublicGallery\n isLegacy\n isOwner\n isPublic\n isQRCodeScanned\n isLiveTesting\n projectName\n settings{\n teamId\n appName\n packageName\n icon\n autoIncrementVersion\n ignoreNotchArea\n notchAreaColor\n androidVersionName\n androidVersionCode\n iosVersionNumber\n iosBuildNumber\n firebaseAPIKey\n firebaseDatabaseURL\n stripePublishableKeyTest\n stripePublishableKeyLive\n stripeAccountId\n stripeTestMode\n isPublic\n description\n mobileTutorial\n pushNotificationAndroidAppId\n pushNotificationIOSAppId\n pushNotificationGeolocationEnabled\n yandexAPIKey\n imageRecognizerServerURL\n imageRecognizerSubscriptionKey\n cloudName\n cloudinaryAPIKey\n cloudinaryAPISecret\n permissions\n googleMapAPIKeyAndroid\n googleMapAPIKeyIOS\n googleOAuthiOSClientID\n googleOAuthiOSURLScheme\n googleOAuthWebClientID\n appleOAuthWebClientID\n appleOAuthWebRedirectURI\n admobAppIdIOS\n admobAppIdAndroid\n admobUserTrackingUsageDescription\n __typename\n}\n projectSettings{\n teamId\n appName\n packageName\n icon\n autoIncrementVersion\n ignoreNotchArea\n notchAreaColor\n androidVersionName\n androidVersionCode\n iosVersionNumber\n iosBuildNumber\n firebaseAPIKey\n firebaseDatabaseURL\n stripePublishableKeyTest\n stripePublishableKeyLive\n stripeAccountId\n stripeTestMode\n isPublic\n description\n mobileTutorial\n pushNotificationAndroidAppId\n pushNotificationIOSAppId\n pushNotificationGeolocationEnabled\n yandexAPIKey\n imageRecognizerServerURL\n imageRecognizerSubscriptionKey\n cloudName\n cloudinaryAPIKey\n cloudinaryAPISecret\n permissions\n googleMapAPIKeyAndroid\n googleMapAPIKeyIOS\n googleOAuthiOSClientID\n googleOAuthiOSURLScheme\n googleOAuthWebClientID\n appleOAuthWebClientID\n appleOAuthWebRedirectURI\n admobAppIdIOS\n admobAppIdAndroid\n admobUserTrackingUsageDescription\n __typename\n}\n hasAdmob\n hasBluetoothLowEnergy\n hasPushNotification\n hasAssistant\n storageSize\n dataSourceLinks{\n id\n dataSource{\n id\n name\n configuration{\n id\n type\n __typename\n}\n collections{\n id\n name\n label\n fields{\n id\n name\n label\n type\n __typename\n}\n __typename\n}\n __typename\n}\n __typename\n}\n localDataSources\n customProperties{\n uuid\n name\n componentType\n type\n defaultValue\n __typename\n}\n appId\n modules{\n id\n name\n type\n blockly\n components\n apiComponents\n isApi\n projectName\n timeSaved\n assets\n customProperties{\n uuid\n name\n componentType\n type\n defaultValue\n __typename\n}\n customEvents{\n uuid\n parameters\n name\n __typename\n}\n customMethods{\n uuid\n parameters\n name\n hasOutput\n __typename\n}\n __typename\n}\n usesDragDropUi\n totalCopy\n totalStar\n starAction\n variables\n webAppSettings{\n appLink\n createdAt\n hasPhoneFrame\n isVisible\n webAppId\n __typename\n}\n webCompanionSettings{\n customDomain{\n checkedAt\n domain\n verifiedAt\n __typename\n}\n icon\n webAppId\n __typename\n}\n frontendProperties{\n componentTreeCollapsedMap\n __typename\n}\n defaultDesignerDevice\n defaultDesignerOrientation\n readOnly\n shares\n versions\n schemaVersion\n organization\n projectSnapshotsMetaData{\n snapshot{\n id\n projectSnapshotParentId\n __typename\n}\n title\n createdAt\n isCurrentVersion\n numberOfScreens\n isAutoSnapshot\n archiveFilename\n creator{\n username\n __typename\n}\n __typename\n}\n projectSnapshotParentId\n projectSnapshotParent{\n id\n projectSnapshotsMetaData{\n snapshot{\n id\n projectSnapshotParentId\n __typename\n}\n title\n createdAt\n isCurrentVersion\n numberOfScreens\n isAutoSnapshot\n archiveFilename\n creator{\n username\n __typename\n}\n __typename\n}\n __typename\n}\n updatedAt\n username\n __typename\n}\n user{\n id\n __typename\n}\n}\n",
        },
    }


def build_push_request(project_id: str, project: dict, config: dict) -> dict:
    return {
        "url": "https://x.thunkable.com/project/updatecontent",
        "cookies": {"thunk_token": config["thunk_token"]},
        "json": {
            "projectOrModuleId": project_id,
            "checkHash": False,
            "projectnewcontent": project["data"]["project"],
        },
    }


def safe_clean_path(path: Path) -> None:
    path.mkdir(exist_ok=True)
    if list(path.iterdir()):
        print("After this operation, the following files will be permanently deleted.")
        for f in path.iterdir():
            print("\t", f)
        ans = input("Do you want to continue [Y/n]? ").lower()
        if ans != "y":
            exit(0)
    shutil.rmtree(path=path, ignore_errors=True)
    path.mkdir(exist_ok=True)


def pull(project_id: str, path: Path, modular: bool, clean: bool) -> None:
    logging.debug("Pulling with")
    logging.debug(f"\tproject_id = {project_id}")
    logging.debug(f"\tpath = {path}")
    logging.debug(f"\tmodular = {modular}")
    logging.debug(f"\tclean = {clean}")
    
    config = safe_read_config()
    logging.debug("Loaded configuration data")
    logging.debug(f"\tconfig = {config}")

    request = build_pull_request(project_id=project_id, config=config)
    logging.debug("Built request")
    logging.debug(f"\trequest = {request}")

    r = requests.post(**request)
    logging.debug("Sent request")
    logging.debug(f"\tr.content = {r.content}")

    if b"project" not in r.content:
        logging.fatal("Failed to pull Thunkable project.")
        logging.info("The project_id might be invalid. Check that the project_id is valid.")
        logging.info("The thunk_token might have expired. Reset the thunk_token.")
        exit(1)
    
    project = load_json(r.content)
    logging.debug(f"\tproject = {project}")

    if "errors" in project:
        logging.fatal("Failed to pull Thunkable project.")
        logging.info("The project_id might be invalid. Check that the project_id is valid.")
        logging.info("The thunk_token might have expired. Reset the thunk_token.")
        exit(1)

    if clean:
        project = to_clean_project(project=project)
        logging.debug("Cleaned project")
        logging.debug(f"\tproject = {project}")

    safe_clean_path(path=path)

    if modular:
        modular_project = to_modular_project(project=project)
        logging.debug("Built modular project")
        logging.debug(f"\tmodular_project = {modular_project}")
        write_modular_project(modular_project=modular_project, project_path=path)
    else:
        path.joinpath("meta.json").write_text(dump_json(project))


def push(project_id: str, path: str, modular: bool) -> None:
    logging.debug("Pushing with")
    logging.debug(f"\tproject_id = {project_id}")
    logging.debug(f"\tpath = {path}")
    logging.debug(f"\tmodular = {modular}")

    config = safe_read_config()
    logging.debug("Loaded configuration data")
    logging.debug(f"\tconfig = {config}")

    if modular:
        modular_project = read_modular_project(project_path=path)
        logging.debug("Loaded modular project")
        logging.debug(f"\tmodular_project = {modular_project}")

        project = from_modular_project(modular_project=modular_project)
        logging.debug("Built project")
        logging.debug(f"\tproject = {project}")
    else:
        project = load_json(path.joinpath("meta.json").read_text())
        logging.debug("Loaded project")
        logging.debug(f"\tproject = {project}")
    
    request = build_push_request(project_id=project_id, project=project, config=config)
    logging.debug("Built request")
    logging.debug(f"\trequest = {request}")

    r = requests.post(**request)
    logging.debug("Sent request")
    logging.debug(f"\tr.content = {r.content}")

    if b"hash" not in r.content:
        logging.fatal("Failed to push Thunkable project.")
        logging.info("The project_id might be invalid. Check that the project_id is valid.")
        logging.info("The thunk_token might have expired. Reset the thunk_token.")
        exit(1)


def configure(variable: str, value: str) -> None:
    try:
        config = load_json(CONFIG_PATH.read_text())
    except Exception as e:
        config = {}
    config[variable] = value
    CONFIG_PATH.write_text(dump_json(config))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Thunkd",
        description="Pull and push Thunkable projects."
    )
    subparsers = parser.add_subparsers(metavar="command", required=True)

    pull_parser = subparsers.add_parser("pull")
    pull_parser.add_argument("project_id", type=str)
    pull_parser.add_argument("path", type=Path)
    pull_parser.add_argument('--modular', required=False, default=True, action=argparse.BooleanOptionalAction)
    pull_parser.add_argument('--clean', required=False, default=True, action=argparse.BooleanOptionalAction)
    pull_parser.set_defaults(func=pull)

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("project_id", type=str)
    push_parser.add_argument("path", type=Path)
    push_parser.add_argument('--modular', required=False, default=True, action=argparse.BooleanOptionalAction)
    push_parser.set_defaults(func=push)

    configure_parser = subparsers.add_parser("set")
    configure_parser.add_argument("variable", type=str, choices={"thunk_token"})
    configure_parser.add_argument("value", type=str)
    configure_parser.set_defaults(func=configure)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    kwargs = vars(args).copy()
    kwargs.pop("func")
    args.func(**kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
