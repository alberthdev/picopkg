import os
import unittest
from picopkg import picopkg

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

class DepTests(unittest.TestCase):
    def test_load_file(self):
        picopkg.read_cfg(picopkg_conf="yaml/missing_deps.yaml")
        picopkg.read_cfg(picopkg_conf="yaml/bare_deps.yaml")
        picopkg.read_cfg(picopkg_conf="yaml/cyclic_deps.yaml")
    
    def test_missing_deps(self):
        cfg = picopkg.read_cfg(picopkg_conf="yaml/missing_deps.yaml")
        state = {}
        with self.assertRaises(RuntimeError) as ctx:
            picopkg.parse_cfg(cfg, state)
    
    def test_dep_resolution(self):
        cfg = picopkg.read_cfg(picopkg_conf="yaml/bare_deps.yaml")
        state = {}
        task_list = picopkg.parse_cfg(cfg, state)
        
        self.assertEquals(len(task_list), 2)
        self.assertEquals(len(task_list[0]), 2)
        self.assertEquals(sorted([x["__name__"] for x in task_list[0]]), sorted(["b", "y"]))
        self.assertEquals(len(task_list[1]), 2)
        self.assertEquals(sorted([x["__name__"] for x in task_list[1]]), sorted(["a", "x"]))
        
        self.assertEquals(sorted(state["cfgs"].keys()), sorted(["a", "b", "x", "y"]))
        
        print("state", state)
    
    def test_dep_resolution_completed_tasks(self):
        cfg = picopkg.read_cfg(picopkg_conf="yaml/bare_deps.yaml")
        state = {}
        picopkg.parse_cfg(cfg, state)
        
        # Finish y
        state["completed"].append("y")
        task_list = picopkg.generate_task_list(state)
        
        self.assertEquals(len(task_list), 2)
        self.assertEquals(len(task_list[0]), 2)
        self.assertEquals(sorted([x["__name__"] for x in task_list[0]]), sorted(["b", "x"]))
        self.assertEquals(len(task_list[1]), 1)
        self.assertEquals(sorted([x["__name__"] for x in task_list[1]]), sorted(["a"]))
        
        # Finish b
        state["completed"].append("b")
        task_list = picopkg.generate_task_list(state)
        
        self.assertEquals(len(task_list), 1)
        self.assertEquals(len(task_list[0]), 2)
        self.assertEquals(sorted([x["__name__"] for x in task_list[0]]), sorted(["a", "x"]))
        
        # Finish a
        state["completed"].append("a")
        task_list = picopkg.generate_task_list(state)
        
        self.assertEquals(len(task_list), 1)
        self.assertEquals(len(task_list[0]), 1)
        self.assertEquals(sorted([x["__name__"] for x in task_list[0]]), sorted(["x"]))
        
        # Finish x
        state["completed"].append("x")
        task_list = picopkg.generate_task_list(state)
        
        self.assertEquals(len(task_list), 0)
    
    def test_dep_resolution_completed_tasks_invalid(self):
        cfg = picopkg.read_cfg(picopkg_conf="yaml/bare_deps.yaml")
        state = {}
        picopkg.parse_cfg(cfg, state)
        
        # Finish x... but y is a dep of x, and it's not complete!
        state["completed"] = ["x"]
        with self.assertRaises(RuntimeError) as ctx:
            task_list = picopkg.generate_task_list(state)
        
        # Finish y - this is OK
        state["completed"] = ["y"]
        task_list = picopkg.generate_task_list(state)
        
        # Finish x and y - this is OK
        state["completed"] = ["x", "y"]
        task_list = picopkg.generate_task_list(state)
        
        # Finish a... but b is a dep of a, and it's not complete!
        state["completed"] = ["a"]
        with self.assertRaises(RuntimeError) as ctx:
            task_list = picopkg.generate_task_list(state)
        
        # Finish b - this is OK
        state["completed"] = ["b"]
        task_list = picopkg.generate_task_list(state)
        
        # Finish a and b - this is OK
        state["completed"] = ["a", "b"]
        task_list = picopkg.generate_task_list(state)
    
    def test_cyclic_deps(self):
        cfg = picopkg.read_cfg(picopkg_conf="yaml/cyclic_deps.yaml")
        state = {}
        with self.assertRaises(RuntimeError) as ctx:
            picopkg.parse_cfg(cfg, state)

def main():
    unittest.main()

if __name__ == "__main__":
    main()
