import os
import copy
import json
import glob
import logging
import argparse
import requests


def dump_json(data: dict) -> str:
    return json.dumps(data, indent=4)


def dump_xml(data: str) -> str:
    return data


def load_json(data: str) -> str:
    return json.loads(data)


def load_xml(data: str) -> str:
    return data


def write(file_path: str, data: str) -> None:
    with open(file_path, "w") as f:
        f.write(data)


def read(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


def build_config_path() -> str:
    script_dir = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(script_dir, "thunkd_py_config.json")


def read_config() -> dict:
    path = build_config_path()
    return load_json(read(file_path=path))


def write_config(config: dict) -> None:
    path = build_config_path()
    write(file_path=path, data=dump_json(config))


def read_modular_project(project_path: str) -> dict:
    modular_project = {}
    ext_to_load = {".json": load_json, ".xml": load_xml}
    search_path = os.path.join(project_path, "*.*")
    for file_path in glob.glob(search_path):
        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_name)
        load_func = ext_to_load[ext]
        modular_project[file_name] = load_func(read(file_path=file_path))
    return modular_project


def write_modular_project(project_path: str, modular_project: dict) -> None:
    os.makedirs(project_path, exist_ok=True)
    ext_to_dump = {".json": dump_json, ".xml": dump_xml}
    for file_name, data in modular_project.items():
        _, ext = os.path.splitext(file_name)
        dump_func = ext_to_dump[ext]
        write(
            file_path=os.path.join(project_path, file_name), 
            data=dump_func(data),
        )


def to_modular_project(project: dict) -> dict:
    project = copy.deepcopy(project)

    modular_project = {}
    iproject = project["data"]["project"]

    screen_ids = []
    for screen in iproject["components"]["children"]:
        screen_id = screen["id"]
        file_path = f"{screen_id}.json"
        modular_project[file_path] = screen
        screen_ids.append(screen_id)
    iproject["components"]["children"] = screen_ids

    for screen_id in iproject["blockly"]:
        if "xml" in iproject["blockly"][screen_id]:
            file_path = f"{screen_id}.xml"
            modular_project[file_path] = iproject["blockly"][screen_id]["xml"]
            iproject["blockly"][screen_id]["xml"] = ""
    
    modular_project["meta.json"] = project
    return modular_project


def from_modular_project(modular_project: dict) -> dict:
    modular_project = copy.deepcopy(modular_project)
    
    project = modular_project["meta.json"]
    del modular_project["meta.json"]

    iproject = project["data"]["project"]
    for file_path, data in modular_project.items():
        screen_id, ext = os.path.splitext(os.path.basename(file_path))
        assert ext in [".json", ".xml"]
        if ext == ".json":
            idx = iproject["components"]["children"].index(screen_id)
            iproject["components"]["children"][idx] = data
        elif ext == ".xml":
            iproject["blockly"][screen_id]["xml"] = data
    
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


def pull(project_id: str, file_path: str, modular: bool, clean: bool) -> None:
    logging.debug("Pulling with")
    logging.debug(f"\tproject_id = {project_id}")
    logging.debug(f"\tfile_path = {file_path}")
    logging.debug(f"\tmodular = {modular}")
    logging.debug(f"\tclean = {clean}")

    assert not (modular and not clean)
    
    config = read_config()
    logging.debug("Loaded configuration data")
    logging.debug(f"\tconfig = {config}")

    request = build_pull_request(project_id=project_id, config=config)
    logging.debug("Built request")
    logging.debug(f"\trequest = {request}")

    r = requests.post(**request)
    logging.debug("Sent request")
    logging.debug(f"\tr.content = {r.content}")

    project = load_json(r.content)
    logging.debug(f"\tproject = {project}")

    if clean:
        project = to_clean_project(project=project)
        logging.debug("Cleaned project")
        logging.debug(f"\tproject = {project}")

    if modular:
        modular_project = to_modular_project(project=project)
        logging.debug("Built modular project")
        logging.debug(f"\tmodular_project = {modular_project}")
        write_modular_project(modular_project=modular_project, project_path=file_path)
    else:
        write(file_path=file_path, data=dump_json(project))


def push(project_id: str, file_path: str, modular: bool) -> None:
    logging.debug("Pushing with")
    logging.debug(f"\tproject_id = {project_id}")
    logging.debug(f"\tfile_path = {file_path}")
    logging.debug(f"\tmodular = {modular}")

    config = read_config()
    logging.debug("Loaded configuration data")
    logging.debug(f"\tconfig = {config}")

    if modular:
        modular_project = read_modular_project(project_path=file_path)
        logging.debug("Loaded modular project")
        logging.debug(f"\tmodular_project = {modular_project}")

        project = from_modular_project(modular_project=modular_project)
        logging.debug("Built project")
        logging.debug(f"\tproject = {project}")
    else:
        project = load_json(read(file_path=file_path))
        logging.debug("Loaded project")
        logging.debug(f"\tproject = {project}")
    
    request = build_push_request(project_id=project_id, project=project, config=config)
    logging.debug("Built request")
    logging.debug(f"\trequest = {request}")

    r = requests.post(**request)
    logging.debug("Sent request")
    logging.debug(f"\tr.content = {r.content}")


def configure(variable: str, value: str) -> None:
    try:
        config = read_config()
    except Exception as e:
        config = {}
    config[variable] = value
    write_config(config=config)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Thunkd",
        description="Pull and push Thunkable projects."
    )
    subparsers = parser.add_subparsers()

    pull_parser = subparsers.add_parser("pull")
    pull_parser.add_argument("project_id", type=str)
    pull_parser.add_argument("file_path", type=str)
    pull_parser.add_argument('--modular', required=False, default=True, action=argparse.BooleanOptionalAction)
    pull_parser.add_argument('--clean', required=False, default=True, action=argparse.BooleanOptionalAction)
    pull_parser.set_defaults(func=pull)

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("project_id", type=str)
    push_parser.add_argument("file_path", type=str)
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
    logging.basicConfig(level=logging.DEBUG)
    main()