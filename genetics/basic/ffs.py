#!/usr/bin/env python
# -*- coding: utf-8 -*-

def fitness_func_1(bit_sum, l):
    return (pow(((bit_sum *1.0)/ pow(2.0, l)), 10))


def fitness_func_2(bit_sum, l):
    return (pow(((1.0 - bit_sum) / pow(2.0, l)), 10))
