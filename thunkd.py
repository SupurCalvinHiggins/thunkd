import os
import json
import requests
from argparse import ArgumentParser


def purge(data: dict) -> dict:
    del data["data"]["user"]
    project = data["data"]["project"]
    del project["id"]
    for key in project["blockly"].keys():
        del project["blockly"][key]["code"]
        del project["blockly"][key]["appVariableDefCode"]
    del project["blocklyStringLength"]
    del project["componentStringLength"]
    del project["createdAt"]
    del project["email"]
    del project["hash"]
    del project["isArchiveProjectFileUsed"]
    del project["isHiddenFromPublicGallery"]
    del project["isLegacy"]
    del project["isOwner"]
    del project["isPublic"]
    del project["isQRCodeScanned"]
    del project["isLiveTesting"]
    del project["settings"]["packageName"]
    del project["projectSettings"]["packageName"]
    del project["appId"]
    del project["readOnly"]
    del project["shares"]
    del project["versions"]
    del project["schemaVersion"]
    del project["projectSnapshotsMetaData"]
    del project["projectSnapshotParentId"]
    del project["projectSnapshotParent"]
    del project["updatedAt"]
    del project["username"]
    return data


def build_cookies() -> dict[str, str]:
    config = read_config()
    return {
        "thunk_token": config["thunk_token"],
    }


def build_pull_payload(project_id: str) -> dict:
    return {
        "operationName": "Project",
        "variables": {
            "id": project_id,
        },
        "query": "query Project($id:ID!,$archiveFilename:String){\n project(id:$id,archiveFilename:$archiveFilename){\n id\n apiComponents\n assets\n backendUpgradeVersion\n blockly\n blocklyStringLength\n categories\n components\n componentStringLength\n createdAt\n figmaComponents\n description\n email\n hash\n icon\n isArchiveProjectFileUsed\n isHiddenFromPublicGallery\n isLegacy\n isOwner\n isPublic\n isQRCodeScanned\n isLiveTesting\n projectName\n settings{\n teamId\n appName\n packageName\n icon\n autoIncrementVersion\n ignoreNotchArea\n notchAreaColor\n androidVersionName\n androidVersionCode\n iosVersionNumber\n iosBuildNumber\n firebaseAPIKey\n firebaseDatabaseURL\n stripePublishableKeyTest\n stripePublishableKeyLive\n stripeAccountId\n stripeTestMode\n isPublic\n description\n mobileTutorial\n pushNotificationAndroidAppId\n pushNotificationIOSAppId\n pushNotificationGeolocationEnabled\n yandexAPIKey\n imageRecognizerServerURL\n imageRecognizerSubscriptionKey\n cloudName\n cloudinaryAPIKey\n cloudinaryAPISecret\n permissions\n googleMapAPIKeyAndroid\n googleMapAPIKeyIOS\n googleOAuthiOSClientID\n googleOAuthiOSURLScheme\n googleOAuthWebClientID\n appleOAuthWebClientID\n appleOAuthWebRedirectURI\n admobAppIdIOS\n admobAppIdAndroid\n admobUserTrackingUsageDescription\n __typename\n}\n projectSettings{\n teamId\n appName\n packageName\n icon\n autoIncrementVersion\n ignoreNotchArea\n notchAreaColor\n androidVersionName\n androidVersionCode\n iosVersionNumber\n iosBuildNumber\n firebaseAPIKey\n firebaseDatabaseURL\n stripePublishableKeyTest\n stripePublishableKeyLive\n stripeAccountId\n stripeTestMode\n isPublic\n description\n mobileTutorial\n pushNotificationAndroidAppId\n pushNotificationIOSAppId\n pushNotificationGeolocationEnabled\n yandexAPIKey\n imageRecognizerServerURL\n imageRecognizerSubscriptionKey\n cloudName\n cloudinaryAPIKey\n cloudinaryAPISecret\n permissions\n googleMapAPIKeyAndroid\n googleMapAPIKeyIOS\n googleOAuthiOSClientID\n googleOAuthiOSURLScheme\n googleOAuthWebClientID\n appleOAuthWebClientID\n appleOAuthWebRedirectURI\n admobAppIdIOS\n admobAppIdAndroid\n admobUserTrackingUsageDescription\n __typename\n}\n hasAdmob\n hasBluetoothLowEnergy\n hasPushNotification\n hasAssistant\n storageSize\n dataSourceLinks{\n id\n dataSource{\n id\n name\n configuration{\n id\n type\n __typename\n}\n collections{\n id\n name\n label\n fields{\n id\n name\n label\n type\n __typename\n}\n __typename\n}\n __typename\n}\n __typename\n}\n localDataSources\n customProperties{\n uuid\n name\n componentType\n type\n defaultValue\n __typename\n}\n appId\n modules{\n id\n name\n type\n blockly\n components\n apiComponents\n isApi\n projectName\n timeSaved\n assets\n customProperties{\n uuid\n name\n componentType\n type\n defaultValue\n __typename\n}\n customEvents{\n uuid\n parameters\n name\n __typename\n}\n customMethods{\n uuid\n parameters\n name\n hasOutput\n __typename\n}\n __typename\n}\n usesDragDropUi\n totalCopy\n totalStar\n starAction\n variables\n webAppSettings{\n appLink\n createdAt\n hasPhoneFrame\n isVisible\n webAppId\n __typename\n}\n webCompanionSettings{\n customDomain{\n checkedAt\n domain\n verifiedAt\n __typename\n}\n icon\n webAppId\n __typename\n}\n frontendProperties{\n componentTreeCollapsedMap\n __typename\n}\n defaultDesignerDevice\n defaultDesignerOrientation\n readOnly\n shares\n versions\n schemaVersion\n organization\n projectSnapshotsMetaData{\n snapshot{\n id\n projectSnapshotParentId\n __typename\n}\n title\n createdAt\n isCurrentVersion\n numberOfScreens\n isAutoSnapshot\n archiveFilename\n creator{\n username\n __typename\n}\n __typename\n}\n projectSnapshotParentId\n projectSnapshotParent{\n id\n projectSnapshotsMetaData{\n snapshot{\n id\n projectSnapshotParentId\n __typename\n}\n title\n createdAt\n isCurrentVersion\n numberOfScreens\n isAutoSnapshot\n archiveFilename\n creator{\n username\n __typename\n}\n __typename\n}\n __typename\n}\n updatedAt\n username\n __typename\n}\n user{\n id\n __typename\n}\n}\n",
    }


def build_push_payload(project_id: str, file_path: str) -> dict:
    with open(file_path, "rb") as f:
        return {
            "projectOrModuleId": project_id,
            "checkHash": False,
            "projectnewcontent": json.load(f)["data"]["project"],
        }


def build_config_path() -> str:
    script_dir = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(script_dir, "thunkd_py_config.json")


def read_config() -> dict:
    path = build_config_path()
    with open(path, "rb") as f:
        return json.load(f)


def write_config(config: dict) -> None:
    path = build_config_path()
    with open(path, "w") as f:
        json.dump(config, f)


def pull(project_id: str, file_path: str, verbose: bool) -> None:

    # Build the cookies and payload.
    cookies = build_cookies()
    payload = build_pull_payload(project_id=project_id)
    if verbose:
        print(f"payload = {payload}")
        print(f"cookies = {cookies}")

    # Download the project.
    r = requests.post(
        "https://x.thunkable.com/graphql",
        cookies=cookies,
        json=payload,
    )
    if verbose:
        print(f"r.content = {r.content}")
        print(f"r.cookies = {r.cookies}")
        print(f"r.headers = {r.headers}")
        print(f"r.status_code = {r.status_code}")

    # Write the output.
    with open(file_path, "w") as f:
        json.dump(purge(json.loads(r.content)), f, indent=4)


def push(project_id: str, file_path: str, verbose: bool) -> None:

    # Build the cookies and payload.
    cookies = build_cookies()
    payload = build_push_payload(project_id=project_id, file_path=file_path)
    if verbose:
        print(f"payload = {payload}")
        print(f"cookies = {cookies}")

    # Push the project.
    r = requests.post(
        "https://x.thunkable.com/project/updatecontent",
        cookies=cookies,
        json=payload,
    )
    if verbose:
        print(f"r.content = {r.content}")
        print(f"r.cookies = {r.cookies}")
        print(f"r.headers = {r.headers}")
        print(f"r.status_code = {r.status_code}")


def configure(variable: str, value: str) -> None:
    try:
        config = read_config()
    except Exception as e:
        config = {}
    config[variable] = value
    config = write_config(config=config)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="Thunkable Download Tool",
        description="Download Thunkable programs."
    )
    subparsers = parser.add_subparsers()

    pull_parser = subparsers.add_parser("pull")
    pull_parser.add_argument("project_id", type=str)
    pull_parser.add_argument("file_path", type=str)
    pull_parser.add_argument("--verbose", required=False, type=bool, default=False)
    pull_parser.set_defaults(func=pull)

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("project_id", type=str)
    push_parser.add_argument("file_path", type=str)
    push_parser.add_argument("--verbose", required=False, type=bool, default=False)
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
    main()