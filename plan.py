import argparse
import numpy as np

from net.cell import TrainedCell
from net.optimization import ActionOptimizer
from hard.domains import HVAC, NAVI, RESERVOIR
from hard.specification import hvac_settings, reservoir_settings, navi_settings
from hard.instance import hvac3_instance, hvac6_instance, hvac60_instance, reservoir3_instance, \
    reservoir4_instance, navi8_instance, navi10_instance, reservoir10_instance, navi10_instance_small
from utils.argument import check_int_positive, check_float_positive
from utils.io import load_pickle, load_csv, save_csv

domains = {
    "Navigation": NAVI,
    "Reservoir": RESERVOIR,
    "HVAC": HVAC
}

settings = {
    "Navigation": navi_settings,
    "Reservoir": reservoir_settings,
    "HVAC": hvac_settings
}

instances = {
    "HVAC6": hvac6_instance,
    "HVAC3": hvac3_instance,
    "HVAC60": hvac60_instance,
    "Reservoir3": reservoir3_instance,
    "Reservoir4": reservoir4_instance,
    "Reservoir10": reservoir10_instance,
    "Navigation10": navi10_instance,
    "Navigation10s": navi10_instance_small, # Small step instance
    "Navigation8": navi8_instance,
}

def constaint(s):
    try:
        num = float(s)
        return num
    except:
        raise argparse.ArgumentTypeError("constraint error")


def main(args):

    domain_inst = domains[args.domain](batch_size=args.batch,
                                       instance_settings=instances[args.instance],
                                       default_settings=settings[args.domain])

    pretrained_weights = load_pickle(args.weight, 'weight')
    normalization = load_csv(args.weight, 'normalization')
    normalization[1][normalization[1] == 0] = 1

    optimizer = ActionOptimizer(num_step=args.horizon,
                                num_act=args.action,
                                batch_size=args.batch,
                                domain_settings=domain_inst,
                                num_state_units=args.state,
                                num_reward_units=args.state+1,
                                num_hidden_units=args.neuron,
                                num_hidden_layers=args.layer,
                                dropout=0.1,
                                pretrained=pretrained_weights,
                                normalize=normalization,
                                learning_rate=0.01,
                                action_mean=5,
                                )

    if args.init is not 'None':
        initial_state = np.tile(load_csv("", args.init), (args.batch, 1))
        optimizer.set_initial_state(initial_state)

    # action constraint need to be pre-defined
    # if args.domain == 'HVAC':
    #     action_constraints = [0, 10]
    # elif args.domain == 'Navigation':
    #     action_constraints = [-1, 1]
    # else:
    #     action_constraints = None

    if args.constraint:
        action_constraints = [args.constraint[0], args.constraint[1]]
        print "Static action constraint:{0}".format(action_constraints)
    else:
        action_constraints = None

    best_actions = optimizer.Optimize(action_constraints, epoch=args.epoch)
    save_csv(best_actions, "", args.resp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tensorflow Planner")

    parser.add_argument('-w', dest='weight', default="weights/hvac/hvac6")
    parser.add_argument('-n', dest='neuron', type=check_int_positive, default=32)
    parser.add_argument('-l', dest='layer', type=check_int_positive, default=2)
    parser.add_argument('-d', dest='domain', default='HVAC')
    parser.add_argument('-i', dest='instance', default='HVAC6')
    parser.add_argument('-b', dest='batch', type=check_int_positive, default=10)
    parser.add_argument('-hz', dest='horizon', type=check_int_positive,  default=20)
    parser.add_argument('-a', dest='action', type=check_int_positive,  default=6)
    parser.add_argument('-s', dest='state', type=check_int_positive, default=6)
    parser.add_argument('-e', dest='epoch', type=check_int_positive, default=300)
    parser.add_argument('--get_state', dest='init', default='temp/state')
    parser.add_argument('--send_action', dest='resp', default='temp/action')
    parser.add_argument('--prefix', dest='head', default='D')
    parser.add_argument('--constraint', dest="constraint", type=constaint, nargs=2)
    args = parser.parse_args()

    main(args)