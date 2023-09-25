import scipy.stats as stats
import numpy as np

def get_posterior_mu(poten_mu, poten_logvar, var_theta):
    T = len(poten_mu)

    a_lst, b_lst = [0], [0]
    for t in reversed(range(T)):
        mu_t = poten_mu[t]
        var_t = np.exp(poten_logvar[t])

        a_t, b_t = a_lst[0], b_lst[0]

        a_t = 1/(1 + var_theta/var_t + (1 - a_t))
        b_t = a_t*(b_t + var_theta/var_t*mu_t)

        a_lst = [a_t] + a_lst
        b_lst = [b_t] + b_lst

    mu_t = [0]
    # var_t = [0]
    for t in range(T):
        a_t, b_t = a_lst[t], b_lst[t]

        mu = a_t*mu_t[-1] + b_t
        mu_t.append(mu)
        # var = var_theta + var_t[-1]*a_t

    mu_t = mu_t[1:]
    return np.array(mu_t)

class Predictor:
    """
        Tracks weekly mood and makes current week's mood estimate
    """

    def __init__(self, mu_init=3, var_week=1/10, var_stud=1/10):
        self.VAR_WEEK = var_week
        self.VAR_STUD = var_stud
        self.q_xt = (mu_init-3, var_week)   # q(x_t|x_t-1)
        self.p_xt = (None, None)            # p(x_t|y_t)
        self.weeks = []
        self.global_weeks = []
        self.mu = []
        self.var = []
        self.n = []

    def bayesian_inf(self, moods):
        """ moods are 1~5 """
        # compute p(x_t|y_<=t) based on q(x_t|y_:t-1)

        moods = np.array(moods) - 3
        g_yt_mu, g_yt_var = np.mean(moods), self.VAR_STUD / len(moods)
        q_xt_mu, q_xt_var = self.q_xt
        p_xt_var = 1 / (1/g_yt_var + 1/q_xt_var)
        p_xt_mu = p_xt_var * (q_xt_mu/q_xt_var + g_yt_mu/g_yt_var)
        return p_xt_mu, p_xt_var

    def make_week_estimate(self, moods, curr_week):
        """ this function must be called in order (of weeks) """
        self.n.append(len(moods))
        if len(moods) == 0:
            self.mu.append(self.mu[-1])
            self.var.append(self.var[-1])
            return

        p_xt_mu, p_xt_var = self.bayesian_inf(moods)
        #  update q(x_t+1|y_:t)
        self.q_xt = (p_xt_mu, p_xt_var + self.VAR_WEEK)

        self.mu.append(p_xt_mu)
        self.var.append(p_xt_var)
        self.weeks.append(curr_week)

    def make_onetime_pred(self, moods):
        p_xt_mu, _ = self.bayesian_inf(moods)
        return p_xt_mu

    def make_all_estimates(self, ratings, weeks):
        for i, rating in enumerate(ratings):
            self.make_week_estimate(rating, weeks[i])

class VarPredictor(Predictor):

    def __init__(self, num_iter, **kwargs):
        super().__init__(**kwargs)
        self.norm_poten_mu = [] # normed poten mu
        self.poten_logvar = []
        self.num_iter = num_iter
        self.phi = stats.norm().pdf
        self.PHI = stats.norm().cdf

    def _tn_normed_E(self, ratings):

        ratings = np.array(ratings) - 3

        PHI_l = self.PHI(ratings - 3.5)
        PHI_l[ratings == 1] = 0

        PHI_h = self.PHI(ratings - 2.5)
        PHI_h[ratings == 5] = 1

        phi_l = self.phi(ratings - 3.5)
        phi_l[ratings == 1] = 0

        phi_h = self.phi(ratings - 2.5)
        phi_h[ratings == 5] =  0

        norm_mu = -(phi_h - phi_l)/(PHI_h - PHI_l)
        return np.mean(norm_mu)

    def make_onetime_pred(self, ratings):

        normed_E_r = self._tn_normed_E(ratings)
        poten_logvar = -np.log(len(ratings)) # assumes standard normal

        mean_mu = np.zeros(len(self.norm_poten_mu)+1)
        norm_poten_mu = np.array(self.norm_poten_mu + [normed_E_r])
        for i in range(self.num_iter):
            poten_mu = mean_mu + norm_poten_mu
            mean_mu = get_posterior_mu(poten_mu, poten_logvar, self.var_week)

        return mean_mu

    def make_all_estimates(self, ratings, weeks):

        norm_poten_mu = np.array([self._tn_normed_E(week_l) for week_l in ratings])
        poten_logvar = np.array([-np.log(len(week_l)) for week_l in ratings]) # assumes standard normal

        mean_mu = np.zeros_like(norm_poten_mu)
        for i in range(self.num_iter):
            poten_mu = mean_mu + norm_poten_mu
            mean_mu = get_posterior_mu(poten_mu, poten_logvar, self.VAR_WEEK)

        self.mu = mean_mu.tolist()
        return mean_mu

class IndepBayesPredictor(Predictor):

    def __init__(self, mu_theta, var_stud=1/10, var_theta=1/10):
        self.VAR_STUD = var_stud
        self.MU_THETA = mu_theta
        self.VAR_THETA = var_theta
        self.weeks = []
        self.mu = []
        self.var = []
        self.n = []

    def bayesian_inf(self, moods):
        moods = np.array(moods) - 3

        var = 1 / (1/self.VAR_THETA + len(moods)/self.VAR_STUD)
        mu = var * (self.MU_THETA/self.VAR_THETA + np.sum(moods)/self.VAR_STUD)
        return mu, var

    def make_onetime_pred(self, moods):
        mu, _ = self.bayesian_inf(moods)
        return mu

    def make_week_estimate(self, moods, curr_week):
        """ this function must be called in order (of weeks) """
        self.n.append(len(moods))

        mu, var = self.bayesian_inf(moods)
        self.mu.append(mu)
        self.var.append(var)
        self.weeks.append(curr_week)

class AvgPredictor(Predictor):

    def __init__(self):
        self.weeks = []
        self.mu = []

    def make_onetime_pred(self, moods):
        return np.array(moods).mean() - 3

    def make_week_estimate(self, moods, curr_week):
        self.mu.append(np.array(moods).mean() - 3)
        self.weeks.append(curr_week)

class MedianPredictor(Predictor):

    def __init__(self):
        self.weeks = []
        self.mu = []

    def make_onetime_pred(self, moods):
        return np.median(moods) - 3

    def make_week_estimate(self, moods, curr_week):
        self.mu.append(np.median(moods) - 3)
        self.weeks.append(curr_week)

class MQEPredictor():

    def __init__(self, init_mu, num_weeks):
        self.num_weeks = num_weeks
        self.mid_week_cnt = (num_weeks + 1) // 2
        self.curr_week = 0
        self.curr_est = init_mu - 3
        self.mu = []
        self.weeks = []

    def make_all_estimates(self, ratings, weeks):
        for i in range(len(ratings)):
            self.make_week_estimate(ratings[i], weeks[i])

    def make_week_estimate(self, moods, curr_week):
        if len(self.weeks) == self.mid_week_cnt:
            self.curr_est = np.mean(moods) - 3
        self.weeks.append(curr_week)
        self.mu.append(self.curr_est)

    def make_onetime_pred(self, moods):
        return self.curr_est
    
class ConstantPredictor():

    def __init__(self, init_mu):
        self.curr_week = 0
        self.curr_est = init_mu - 3
        self.mu = []
        self.weeks = []

    def make_all_estimates(self, ratings, weeks):
        for i in range(len(ratings)):
            self.make_week_estimate(ratings[i], weeks[i])

    def make_week_estimate(self, moods, curr_week):
        self.weeks.append(curr_week)
        self.mu.append(self.curr_est)

    def make_onetime_pred(self, moods):
        return self.curr_est

