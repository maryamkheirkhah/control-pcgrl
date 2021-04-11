from gym_pcgrl.envs.probs.zelda_prob import ZeldaProblem
import numpy as np

class MultiGoalZeldaProblem(ZeldaProblem):
    def __init__(self):
        super(MultiGoalZeldaProblem, self).__init__()
        self._max_nearest_enemy = np.ceil(self._width / 2 + 1) * (self._height)
        self._max_path_length = np.ceil(self._width / 2 + 1) * (self._height)
        # like _rewards but for use with ParamRew
        self.weights = {
                'player': 3,
                'key': 3,
                'door': 3,
                'regions': 5,
                'enemies': 1,
                'nearest-enemy':2,
                'path-length': 1,
                }

        self.static_trgs = {
                'enemies': (2, 7),
                'path-length': self._max_path_length,
                'nearest-enemy': (5, self._max_nearest_enemy),
                'regions': 1,
                'player': 1,
                'key': 1,
                'door':1,
                }
        # conditional inputs/targets ( just a default we don't use in the ParamRew wrapper)
        self.cond_trgs = {
                'player': 1,
                'key': 1,
                'door': 1,
                'regions': 1,
                'enemies': 5,
                'nearest-enemy': 7,
                'path-length': 100,
                }
        # boundaries for conditional inputs/targets
        self.cond_bounds = {
                'nearest-enemy': (0, self._max_nearest_enemy),
                'enemies': (0, self._width * self._height - 2), 
                'player': (0, self._width * self._height - 2), 
                'key': (0, self._width * self._height - 2), 
                'door': (0, self._width * self._height - 2), 
                'regions': (0, self._width * self._height / 2),
                                                                                            
                #FIXME: we shouldn't assume a square map here! Find out which dimension is bigger
                # and "snake" along that one
                'path-length': (0, self._max_path_length),  # Upper bound: zig-zag

                                                                                            #   11111111
                                                                                            #   00000001
                                                                                            #   11111111
                                                                                            #   10000000
                                                                                            #   11111111
                }

    # We do these things in the ParamRew wrapper
    def get_episode_over(self, new_stats, old_stats):
        return False

    def get_reward(self, new_stats, old_stats):
        return None

    """
    Get the current stats of the map

    Returns:
        dict(string,any): stats of the current map to be used in the reward, episode_over, debug_info calculations.
        The used status are "reigons": number of connected empty tiles, "path-length": the longest path across the map
    """
    def get_stats(self, map):
        map_locations = get_tile_locations(map, self.get_tile_types())
        map_stats = {
            "player": calc_certain_tile(map_locations, ["player"]),
            "key": calc_certain_tile(map_locations, ["key"]),
            "door": calc_certain_tile(map_locations, ["door"]),
            "enemies": calc_certain_tile(map_locations, ["bat", "spider", "scorpion"]),
            "regions": calc_num_regions(map, map_locations, ["empty", "player", "key", "bat", "spider", "scorpion"]),
            "nearest-enemy": 0,
            "path-length": 0
        }
        if map_stats["player"] > 0:  # and map_stats["regions"] == 1:
            # NOTE: super whack, just taking random player. The RL agent may learn some weird bias about this but the alternatives seem worse.
            p_x,p_y = map_locations["player"][0]
            enemies = []
            enemies.extend(map_locations["spider"])
            enemies.extend(map_locations["bat"])
            enemies.extend(map_locations["scorpion"])
            UPPER_DIST = self._width * self._height * 100
            if len(enemies) > 0:
                dikjstra,_ = run_dikjstra(p_x, p_y, map, ["empty", "player", "key", "bat", "spider", "scorpion"])
                min_dist = UPPER_DIST
                for e_x,e_y in enemies:
                    if dikjstra[e_y][e_x] > 0 and dikjstra[e_y][e_x] < min_dist:
                        min_dist = dikjstra[e_y][e_x]
                if min_dist == UPPER_DIST:
                    min_dist = 0
                map_stats["nearest-enemy"] = min_dist
            # NOTE: BIG CONTROLLABILITY HACK!! We want to provide a reliable path-length signal when possible. So we compute it even on invalid maps,
            # take the least path-length, as with enemies above. And we're greedy, closest key, then closest door. No time for shortest overall path,
            # forget it.
            if map_stats["key"] > 0 and map_stats["door"] > 0:
                d_x,d_y = map_locations["door"][0]
                dikjstra,_ = run_dikjstra(p_x, p_y, map, ["empty", "key", "player", "bat", "spider", "scorpion"])
                min_key_dist = UPPER_DIST
                min_key_coords = None
                for k_x,k_y in map_locations["key"]:
                    key_dist = dikjstra[k_x][k_y]
                    if key_dist > 0 and key_dist < min_key_dist:
                        min_key_dist = key_dist
                        min_key_coords = k_x, k_y

                if min_key_coords and not min_key_dist == UPPER_DIST:
                    map_stats["path-length"] += min_key_dist

                    dikjstra,_ = run_dikjstra(k_x, k_y, map, ["empty", "player", "key", "door", "bat", "spider", "scorpion"])
                    min_door_dist = UPPER_DIST
                    min_door_coords = None
                    for d_x,d_y in map_locations["door"]:
                        door_dist = dikjstra[d_x][d_y]
                        if door_dist > 0 and door_dist < min_door_dist:
                            min_door_dist = door_dist
                            min_door_coords = d_x, d_y

                    if min_door_coords and not min_door_dist == UPPER_DIST:
                        map_stats["path-length"] += min_door_dist

        return map_stats