#!/usr/bin/env python
import logging
import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# Graph:
# Each node can be represented as a key in a dictionary,
# and each node's outgoing edge can be represented as a set
# within the dictionary.
# 
# Example:
#    A
#   / \
#  B   C
# 
# { A: set([B, C]), B: set(), C: set() }
# Storage: O(E + V)

# Dependency Calculation:
# Given a graph of packages and their dependencies, return the optimal
# way of installing each package while satisfying the dependency order.
# 
# Corner cases...
#  * if there are multiple "roots", need to find the roots to start at
#    and determine dependencies accordingly
#    
#    (e.g. there exists a node set such that they are not connected with
#    any other node set, given >1 node sets)
#    
#    Also, finding the "root" in the first place would be ideal, even
#    if there is just a single "root".
#    
#    Solution: attempt to find root via traversing dict keys, 
#    
#       A      D    G
#      / \    / \
#     B   C  E   F
#  * 
# 
# Input/Output:
#  * Simple:
#    B, C, A
#    
#      A
#     / \
#    B   C
#  
#  * Multiple inputs:
#    D, B, C, A
#    
#      A
#     / \
#    B   C
#     \ /
#      D
#  
#  * Circular Dependencies:
#    ERROR (B depends on C which depends on D which depends on... B)
#    
#      A
#     / \
#    B---C
#     \ /
#      D
# 
# Pseudocode...
#   seen_verts = set()
#   
#   for vert in verts:
#     graph[vert]

def strongly_connected_components(graph):
    """
    Tarjan's Algorithm (named for its discoverer, Robert Tarjan) is a graph theory algorithm
    for finding the strongly connected components of a graph.
    
    Based on: http://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
    
    As a bonus, it pops out a reverse toplogical sort!
    
    Created by Dr. Paul Harrison
    
    Sourced from: http://www.logarithmic.net/pfh/blog/01208083168
    Direct link: http://www.logarithmic.net/pfh-files/blog/01208083168/tarjan.py
    
    License: CCO
    """

    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    result = []
    
    def strongconnect(node):
        # set the depth index for this node to the smallest unused index
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
    
        # Consider successors of `node`
        try:
            successors = graph[node]
        except:
            successors = []
        for successor in successors:
            if successor not in lowlinks:
                # Successor has not yet been visited; recurse on it
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node],lowlinks[successor])
            elif successor in stack:
                # the successor is in the stack and hence in the current strongly connected component (SCC)
                lowlinks[node] = min(lowlinks[node],index[successor])
        
        # If `node` is a root node, pop the stack and generate an SCC
        if lowlinks[node] == index[node]:
            connected_component = []
            
            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node: break
            component = tuple(connected_component)
            # storing the result
            result.append(component)
    
    for node in graph:
        if node not in lowlinks:
            strongconnect(node)
    
    return result

def read_cfg(directory, fail = True):
    """Read Picopkg configuration from a directory.
    
    Read Picopkg configuration from a directory, and return the
    resulting configuraton object.
    
    Args:
        directory (str): String specifying the directory to load the
            configuration from.
        fail (bool, optional): Whether to critically fail on error or
            not. If this is set to False, errors will not be printed
            and exceptions will not be raised. Defaults to True.
    
    Returns:
        dict: Resulting configuration object.
    
    Raises:
        OSError: The file was not accessible or readable.
        yaml.YAMLError: The YAML configuration file format was invalid.
    """
    picopkg_conf = os.path.join(directory, "picopkg.yaml")
    
    logging.debug("Attempting to open %s..." % picopkg_conf)
    
    try:
        with open(picopkg_conf, "r") as fh:
            cfg_obj = yaml.safe_load(fh, Loader=Loader)
        
    except OSError:
        if fail:
            logging.exception("Could not open file %s!" % picopkg_conf)
            raise
    except yaml.YAMLError, exc:
        logging.exception("Could not parse YAML from file %s!" % picopkg_conf)
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            logging.error("Error position: (%s:%s)" % (mark.line+1, mark.column+1))
        raise
    
    return cfg_obj

def parse_package_cfg(cfg_obj, graph, fail = True):
    """Parse Picopkg package configuration from a configuration dict.
    
    Parse Picopkg package configuration given its dictionary, and return
    the resulting package object (if any), as well as additional directories
    to search from any subpackages.
    
    Args:
        cfg_obj (dict): Configuration dictionary.
        fail (bool, optional): Whether to critically fail on error or
            not. If this is set to False, errors will not be printed
            and exceptions will not be raised. Defaults to True.
    
    Returns:
        dict: Resulting configuration object.
    
    Raises:
        OSError: The file was not accessible or readable.
        yaml.YAMLError: The YAML configuration file format was invalid.
    """
    
    # Parse pseudocode:
    #   Examine object for package metadata, if it exists:
    #     Add package ID to graph, with dependencies
    #       For each dependency, if it doesn't exist, add to unresolved
    #       list
    #     Add all package information to package dict
    #   
    # 
    

def parse_subpackage_cfg(cfg_obj, graph, fail = True):
    """Parse Picopkg package configuration from a configuration dict.
    
    Parse Picopkg package configuration given its dictionary, and return
    the resulting package object (if any), as well as additional directories
    to search from any subpackages.
    
    Args:
        cfg_obj (dict): Configuration dictionary.
        fail (bool, optional): Whether to critically fail on error or
            not. If this is set to False, errors will not be printed
            and exceptions will not be raised. Defaults to True.
    
    Returns:
        dict: Resulting configuration object.
    
    Raises:
        OSError: The file was not accessible or readable.
        yaml.YAMLError: The YAML configuration file format was invalid.
    """
    
    # Parse pseudocode:
    #   Examine object for package metadata, if it exists:
    #     Add package ID to graph, with dependencies
    #       For each dependency, if it doesn't exist, add to unresolved
    #       list
    #     Add all package information to package dict
    #   
    # 

def parse_cfg():
    """Parse all Picopkg configuration from a configuration dict.
    
    Parse Picopkg package configuration given its dictionary, and return
    the resulting package object (if any), as well as additional
    directories to search from any subpackages.
    
    Args:
        cfg_obj (dict): Configuration dictionary.
        fail (bool, optional): Whether to critically fail on error or
            not. If this is set to False, errors will not be printed
            and exceptions will not be raised. Defaults to True.
    
    Returns:
        dict: Resulting configuration object.
    
    Raises:
        OSError: The file was not accessible or readable.
        yaml.YAMLError: The YAML configuration file format was invalid.
    """
