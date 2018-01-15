#!/usr/bin/env python
import copy
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
    Fixes and improvements by Dries Verdegem
    
    Sourced from: http://www.logarithmic.net/pfh/blog/01208083168
    Direct link: http://www.logarithmic.net/pfh-files/blog/01208083168/tarjan.py
    
    License: CCO
    
    Args:
        graph (dict): a dictionary representing a graph in the form of
            an adjacency list, e.g. vertex i as a key whose value is
            a list of vertices the vertex i connects to.
            (example: { 0: [1], 1: [2] } == 0 -> 1 -> 2)
    
    Returns:
        list of tuples: a list of tuples representing the strongly
            connected components of the given graph, in reverse
            toplogical sort.
    
    Examples:
        >>> strongly_connected_components({0:[1], 1:[2,3]})
        [(2,), (3,), (1,), (0,)]
        
        >>> strongly_connected_components({0:[1], 1:[2,3,0]})
        [(2,), (3,), (1, 0)]
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

class objdict(dict):
    """Object that allows you to use a dictionary via the attributes.
    
    Modified to return None on invalid attributes.
    
    From: https://goodcode.io/articles/python-dict-object/
    """
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            return None

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

def read_cfg(picopkg_conf="picopkg.yaml", fail=True):
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
    
    logging.debug("Attempting to open %s..." % picopkg_conf)
    
    try:
        with open(picopkg_conf, "r") as fh:
            cfg_obj = yaml.safe_load(fh)
        
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
    
    for k in cfg_obj:
        cfg_obj[k]["__file__"] = picopkg_conf
    
    return cfg_obj

def parse_package_cfg(cfg_obj, fail=True):
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
    pass

def describe_task(state, task):
    return "%s (in %s)" % (task, state["cfgs"][task]["__file__"])

def describe_tasks(state, tasks):
    return "[%s]" % (", ".join([describe_task(state, task) for task in tasks]))

def generate_task_list(state):
    # Build final task list!
    # Can we parallelize anything? If so, specify a list of pkg_cfg with
    # multiple elements. Otherwise, just specify one task in the list.
    # e.g. [ [task1], [task2, task3] ]
    task_list = []
    task_list_deps = copy.deepcopy(state["dep_graph"])
    
    scc = list(state["scc"])
    
    # Filter out completed tasks
    scc = [task for task in scc if task not in state["completed"]]
    task_list_deps = {
        task: [task_dep for task_dep in task_deps if task_dep not in state["completed"]]
        for task, task_deps in task_list_deps.items() if task not in state["completed"]
    }
    dep_graph_reversed_without_completed = {
        task: task_deps_on_me for task, task_deps_on_me in state["dep_graph_reversed"].items()
        if task not in state["completed"]
    }
    
    # Validate using reverse if there are any weird completions
    # Find intersections between completed tasks and the reverse dep graph values,
    # aka the intersection between completed tasks and uncompleted task reverse
    # dependencies.
    dep_graph_reversed_without_completed = [
        [set.intersection(set(state["completed"]), set(state["dep_graph_reversed"][task])), task]
        for task in dep_graph_reversed_without_completed
        if set.intersection(set(state["completed"]), set(state["dep_graph_reversed"][task]))
    ]
    
    if dep_graph_reversed_without_completed:
        raise RuntimeError("Completed tasks still have dependencies missing: " +
            ", ".join(["%s depends on %s" % (describe_tasks(state, a[0]), describe_task(state, a[1])) for a in dep_graph_reversed_without_completed]))
    
    while len(scc):
        pkg_id = scc.pop(0)
        
        tasks_available = [k for k in task_list_deps if not len(task_list_deps[k])]
        
        print("Current scc = " + str(scc))
        
        if len(tasks_available) > 1:
            # We can parallelize here!
            new_task = [state["cfgs"][task] for task in tasks_available]
            
            # Remove the parallelized tasks from the scc
            scc = [scc_component for scc_component in scc if scc_component not in tasks_available]
            
            print("New scc = " + str(scc))
            
            # Process dependency resolution
            print(tasks_available)
            for task in tasks_available:
                print("Dep resolution for task = %s" % task)
                
                if task in state["dep_graph_reversed"]:
                    print("dep_graph_reversed[task] = %s" % str(state["dep_graph_reversed"][task]))
                    for pkg_id_depends_on_me in state["dep_graph_reversed"][task]:
                        print("In task_list_deps, removing task %s from package %s" % (task, pkg_id_depends_on_me))
                        task_list_deps[pkg_id_depends_on_me].remove(task)
                else:
                    # Probably root node
                    print("root node")
                
        else:
            print("doing single task instead: %s" % pkg_id)
            new_task = [state["cfgs"][pkg_id]]
            
            # Process dependency resolution
            if pkg_id in state["dep_graph_reversed"]:
                for pkg_id_depends_on_me in state["dep_graph_reversed"][pkg_id]:
                    task_list_deps[pkg_id_depends_on_me].remove(pkg_id)
            else:
                # Probably root node
                print("root node")
        
        # All scheduled, remove them from the list
        for task in tasks_available:
            task_list_deps.pop(task)
        
        task_list.append(new_task)
    
    return task_list

def parse_cfg(cfg_obj, state):
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
    
    all_cfgs = []
    pkg_defs = []
    
    # Load any includes needed
    if "include" in cfg_obj:
        cfgs_to_load = list(cfg_obj["include"])
        all_cfgs = list(cfgs_to_load)
        
        while len(cfgs_to_load):
            picopkg_conf = cfgs_to_load.pop(0)
            
            tmp_cfg_obj = read_cfg(picopkg_conf=picopkg_conf)
            
            if "include" in tmp_cfg_obj:
                new_cfgs = [include for include in tmp_cfg_obj["include"] if include not in all_cfgs]
                cfgs_to_load += new_cfgs
                all_cfgs += new_cfgs
            
            pkg_defs.append(tmp_cfg_obj["pkgs"])
    
    ## Append our package definition
    pkg_defs.append(cfg_obj["pkgs"])
    
    ## Propoagate the __file__ into each package:
    for pkg_def_blob in pkg_defs:
        if "__file__" not in pkg_def_blob:
            raise RuntimeError("No __file__ found for the bundle of package defs!")
        pkg_def_file = pkg_def_blob.pop("__file__")
        for pkg_id, pkg_def in pkg_def_blob.items():
            pkg_def["__file__"] = pkg_def_file
    
    ## Parse the package defs
    if "cfgs" not in state:
        state["cfgs"] = {}
    
    while len(pkg_defs):
        pkg_def_blob = pkg_defs.pop(0)
        print("pkg_def_blob", pkg_def_blob)
        for pkg_id, pkg_def in pkg_def_blob.items():
            if pkg_id in state["cfgs"]:
                print(pkg_def)
                print(state["cfgs"])
                raise RuntimeError("Duplicate package ID %s found in configuration %s! "
                                   "(First defined in: %s)" % 
                                   (pkg_id, pkg_def["__file__"], state["cfgs"][pkg_id]["__file__"]))
            state["cfgs"][pkg_id] = pkg_def
            print("pkg_def", pkg_def)
            state["cfgs"][pkg_id]["__name__"] = pkg_id
    
    ## Compute dependency execution order
    
    # First, build the graph
    dep_graph = {}
    dep_graph_reversed = {}
    
    for pkg_id in state["cfgs"]:
        dep_graph[pkg_id] = (state["cfgs"][pkg_id]["depends"] 
            if "depends" in state["cfgs"][pkg_id]
            else [])
        
        # Build reverse of the graph, e.g. a -> [b,c] becomes b->a, c->a
        # b->a means "b asks who depends on me? a does"
        if "depends" in state["cfgs"][pkg_id]:
            for depend_pkg_id in state["cfgs"][pkg_id]["depends"]:
                if depend_pkg_id not in dep_graph_reversed:
                    dep_graph_reversed[depend_pkg_id] = [pkg_id]
                else:
                    dep_graph_reversed[depend_pkg_id].append(pkg_id)
    
    # Then, get the execution order via computing strongly connected
    # components!
    scc = strongly_connected_components(dep_graph)
    
    # Check to make sure we don't have cyclic dependencies...
    if any(len(scc_ele) > 1 for scc_ele in scc):
        raise RuntimeError("Detected cyclic dependencies: %s" %
            ("; ".join([("%s" % describe_tasks(state, scc_ele))
                            for scc_ele in scc if len(scc_ele) > 1])))
    
    print("scc", scc)
    
    # Reduce the SCC list down to a list of scalars (non-tuples)
    scc = [s[0] for s in scc]
    
    # Check if we have any missing deps
    missing_deps = [s for s in scc if s not in state["cfgs"]]
    
    if missing_deps:
        raise RuntimeError("Missing dependencies: " + ", ".join(missing_deps))
    
    # Save our bits and pieces
    state["dep_graph"] = dep_graph
    state["dep_graph_reversed"] = dep_graph_reversed
    state["scc"] = scc
    
    # Create completed state tracking
    state["completed"] = []
    
    # Return task list
    return generate_task_list(state)
