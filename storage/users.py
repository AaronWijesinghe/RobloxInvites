from storage.database import *

class UserManager:
    def __init__(self, api):
        self.api = api
        self.users = load_data("users.json", None, False, "You must add at least one user to users.json.")

    async def get_user_ids(self):
        user_ids = list(self.users.keys())

        new_user_ids = []
        for id, data in self.users.values():
            if data == {}:
                new_user_ids += [id]

        if len(new_user_ids) == 0:
            return user_ids
        
        req = await self.api.get_user_data(new_user_ids)
        ids = [user["id"] for user in req["data"]]
        unames = [user["name"].lower() for user in req["data"]]
        displaynames = [user["displayName"] for user in req["data"]]

        if len(unames) != len(set(unames)):
            write_to_log("fatal", "Invites can't be checked twice for the same user.")
            print(f"{underline}Invites can't be checked twice for the same user.{end}")
            exit()

        faulty_users = [uid for uid in new_user_ids if uid not in unames]
        if len(faulty_users) > 0:
            write_to_log("fatal", f"These users don't exist: [@{', @'.join(faulty_users)}]")
            print(f"{underline}These users don't exist: [@{', @'.join(faulty_users)}]{end}")
            exit()
        
        username_map = dict(zip(unames, ids))
        displayname_id_map = dict(zip(unames, displaynames))
        new_user_ids = [username_map[user.lower()] for user in new_user_ids]
        new_display_names = [displayname_id_map[user.lower()] for user in new_user_ids]
        for i_index_list, i_user_list in enumerate(new_user_ids):
            self.users[i_user_list]["username"] = new_user_ids[i_index_list]
            self.users[i_user_list]["display_name"] = new_display_names[i_index_list]

        write_to_log("info", f"Added new user IDs: {new_user_ids}")
        save_data(self.users, "users.json")
        user_ids = [user["user_id"] for user in self.users]
        return user_ids