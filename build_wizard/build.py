import os
import sys
import shutil
import platform

gold = "\033[0;33m"
bold = "\033[1m"
faint = "\033[2m"
end = "\033[0m"

op = platform.system()
def clear():
    os.system("clear;clear" if op == "Darwin" else "cls")

if op in ["Darwin", "Windows"]:
    def build():
        clear()
        print(f"{gold}[Build CTWizard]{end}")
        print(f"{bold}Here are the minimum requirements to build CTWizard:{end}")
        print("    - 200MB+ space (app ~55MB, launcher ~2MB, rest is temporary files)")
        print("    - The modules in requirements.txt")
        print("    - CTWizard.py in the (parent) directory of the build script")
        print("    - AppIcon(.icns/.ico), launcher.py, and Info.plist in ./Resources/")
        print("    - Any version of CTWizard (MacOS) or CTWizard v1.0.0+ (Windows)")
        print(f"\n{bold}If you're running Option 1 for a complete install:{end}")
        print("    - ./assets/ with docs.txt, changelog.txt, and donations.json in the (parent) directory of the build script")

        if os.path.exists("../CTWizard.py"):
            CTWizardPath = "../CTWizard.py"
        elif os.path.exists("./CTWizard.py"):
            CTWizardPath = "./CTWizard.py"
        else:
            input("CTWizard.py wasn't found. ")
            return

        version = open(CTWizardPath, "r").read().split("version = \"")[1].split("\"")[0]
        print(f"\nCTWizard Version: {version}")
        input("Press ENTER to start building CTWizard. ")
        modifiedPLIST = open("./Resources/Info.plist", "r").read().replace("0.0.0", version)

        if op == "Darwin":
            if not os.path.exists("./Resources/launcher") and os.path.exists("./Resources/launcher.py"):
                os.system("pyinstaller ./Resources/launcher.py")
                os.system("cp ./dist/launcher/launcher ./Resources/")
                os.system("rm -rf build dist *.spec")

            os.system(f"pyinstaller --windowed {CTWizardPath} --icon ./Resources/AppIcon.icns")
            os.system("cp -r ./dist/CTWizard.app .")
            os.system("cp ./Resources/launcher ./CTWizard.app/Contents/MacOS/")
            for delete in os.listdir("./CTWizard.app/Contents/Resources/"):
                if delete != "AppIcon.icns":
                    os.system(f"rm -rf ./CTWizard.app/Contents/Resources/{delete}")
            os.system("rm -rf ./CTWizard.app/Contents/Frameworks/python3__dot__14")
            open("./CTWizard.app/Contents/Info.plist", "w").write(modifiedPLIST)
            os.system("rm -rf build dist *.spec")
        else:
            os.system(f"pyinstaller {CTWizardPath} --icon ./Resources/AppIcon.ico")
            os.system("xcopy .\\dist\\ct_wizard . /E /Q")
            shutil.rmtree("./build/")
            shutil.rmtree("./dist/")
            os.system("erase *.spec /Q")

    def transfer_to_applications(output=True):
        clear()
        if output:
            print(f"{gold}[Transfer CTWizard to /Applications]{end}")

        if os.path.exists("/Applications/CTWizard.app"):
            os.system("rm -rf /Applications/CTWizard.app")
        os.system("mv CTWizard.app /Applications/")
        if output:
            input("CTWizard.app was moved to the Applications folder. ")

    def delete_from_applications():
        clear()
        print(f"{gold}[Delete CTWizard from /Applications]{end}")
        os.system("rm -rf /Applications/CTWizard.app")
        input("CTWizard.app was deleted from the Applications folder. ")

    while True:
        clear()
        os.chdir(os.path.dirname(__file__))

        app_location = "_internal" if op == "Windows" else "CTWizard.app"
        app_exists = "" if os.path.exists(app_location) else faint
        app_exists_a = "" if os.path.exists("/Applications/CTWizard.app") else faint

        args = sys.argv[1:]
        if len(args) == 0:
            print(f"{gold}[CTWizard Build Tool]{end}")
            print(f"{bold}[1] Install CTWizard from source (Options 2{", 3, and 4" if op == "Darwin" else " and 3"} combined){end}")
            print("[2] Build CTWizard")
            if op == "Darwin":
                print(f"{app_exists}[3] Transfer CTWizard to /Applications (macOS Only){end}")
                print(f"{app_exists_a}[4] Delete CTWizard from /Applications (macOS Only){end}")
            print(f"[{"3" if op == "Windows" else "5"}] Exit")
            option = input("\nSelect an option: ").strip()
        else:
            option = args[-1].strip()

        if not option.isnumeric() or not option in ["1", "2", "3", "4", "5" if op == "Darwin" else "1", "6" if op == "Darwin" else "1"]:
            input("Invalid option. ")
        else:
            option = int(option)

        match option:
            case 1:
                build()
                if op == "Darwin":
                    transfer_to_applications(output=False)
            case 2:
                build()
            case 3:
                if os.path.exists(app_location) and op == "Darwin":
                    transfer_to_applications()
                elif op == "Windows":
                    exit()
            case 4:
                if os.path.exists("/Applications/CTWizard.app") and op == "Darwin":
                    delete_from_applications()
            case 5:
                exit()
        
        if len(args) > 0:
            exit()
else:
    clear()
    input("The build script is not available for Linux at this time. ")
