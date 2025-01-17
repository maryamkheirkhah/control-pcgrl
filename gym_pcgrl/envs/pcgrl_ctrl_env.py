import numpy as np
from gym_pcgrl.envs.pcgrl_env import PcgrlEnv

class PcgrlCtrlEnv(PcgrlEnv):
    def __init__(self, prob="binary_ctrl", rep="narrow", **kwargs):
        super(PcgrlCtrlEnv, self).__init__(prob, rep, **kwargs)
        self.metrics = {}
        print('problem static trgs: {}'.format(self._prob.static_trgs))
        for k in {**self._prob.static_trgs}:
            self.metrics[k] = None
        print('env metrics: {}'.format(self.metrics))
        self.weights = self._prob.weights
        self.cond_bounds = self._prob.cond_bounds
        self.static_trgs = self._prob.static_trgs
        self.width = self._prob._width
        self._max_changes = max(int(1 * self._prob._width * self._prob._height), 1)

    def set_map(self, init_map):
        self._rep._random_start = False
        self._rep._old_map = init_map.copy()

    # FIXME: this isn't necessary right? Dictionary is the same yeah? ....yeah?

    def reset(self):
        obs = super().reset()
        self.metrics = self._rep_stats
        return obs

    def step(self, actions):
        ret = super().step(actions)
        self.metrics = self._rep_stats
        return ret

    def adjust_param(self, **kwargs):
        super().adjust_param(**kwargs)
        if kwargs.get('change_percentage') == -1:
            self._max_changes = np.inf

    def get_max_loss(self, ctrl_metrics=[]):
        '''Upper bound on distance of level from static targets.'''
        net_max_loss = 0
        for k, v in self.static_trgs.items():
            if k in ctrl_metrics:
                continue
            if isinstance(v, tuple):
                max_loss = max(abs(v[0] - self.cond_bounds[k][0]), abs(v[1] - self.cond_bounds[k][1])) * self.weights[k]
            else: max_loss = max(abs(v - self.cond_bounds[k][0]), abs(v - self.cond_bounds[k][1])) * self.weights[k]
            net_max_loss += max_loss
        return net_max_loss
