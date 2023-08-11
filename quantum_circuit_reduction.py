'''
(C) Renata Wong

This code reduces the number of gates in a quantum circuit according to the following rules:
XX = YY = ZZ = HH = I, Sdg x S = S x Sdg = I, CX x CX = II, HZH = X, HXH = Z, SS = Sdg x Sdg = Z
'''

from qiskit import transpile
from qiskit import QuantumCircuit
import numpy as np
from qiskit.converters import circuit_to_dag
from qiskit.transpiler import TransformationPass
from qiskit.dagcircuit import DAGOpNode
from qiskit.circuit import Instruction


class GateReduction(TransformationPass):
    
    """
    A transpiler pass to reduce gate number in a circuit.
    Rules: XX=YY=ZZ=HH=I, SdgS=SSdg=I, CXCX=II
    """

    def run(self, dag):
        
        # take care of cx gates first
        # cx gates may be incorrectly removed when processing nodes according to wires
        # this happens in multi-wire circuits when there are operators between 2 cx gates on one wire 
        # but not on another wire
        nodes = dag.op_nodes()
        for index, node in enumerate(nodes):
            if index+1 < len(nodes):
                if node.op.name == 'cx':
                    next_node = nodes[index+1]
                    if next_node.op.name == node.op.name:
                        if node.qargs == next_node.qargs:
                            dag.remove_op_node(node)
                            dag.remove_op_node(next_node)
                            nodes.remove(node)
                            nodes.remove(next_node)

        # iterate over all operations, wire after wire
        for wire in dag.wires:
            
            # convert iterator nodes_on_wire to a list of nodes
            nodes = list(dag.nodes_on_wire(wire, only_ops = True)) 
            
            for index, node in enumerate(nodes): 

                if node.op.name in ['x', 'y', 'z', 'h']:
                    
                    # warning: dag.node_counter produces incorrect values for our use
                    if index+1 < len(nodes): 
                        next_node = nodes[index+1] 
                        
                        if next_node.op.name == node.op.name:
                            if node.qargs == next_node.qargs:
                                dag.remove_op_node(node)
                                dag.remove_op_node(next_node)
                                nodes.remove(node)
                                nodes.remove(next_node)

                        if index+2 < len(nodes):
                            if node.op.name == 'h' and next_node.op.name == 'z':
                                third_node = nodes[index+2]
                                if third_node.op.name == 'h':
                                    replacement = QuantumCircuit(1)
                                    replacement.x(0)
                                    dag.substitute_node_with_dag(third_node, circuit_to_dag(replacement))
                                    dag.remove_op_node(node)
                                    dag.remove_op_node(next_node)
                                    nodes[index+2] = DAGOpNode(op=Instruction(name='x', num_qubits=1, num_clbits=0, params=[]))
                                    nodes.remove(node)
                                    nodes.remove(next_node)

                        if index+2 < len(nodes):
                            if node.op.name == 'h' and next_node.op.name == 'x':
                                third_node = nodes[index+2]
                                if third_node.op.name == 'h':
                                    replacement = QuantumCircuit(1)
                                    replacement.z(0)
                                    dag.substitute_node_with_dag(third_node, circuit_to_dag(replacement))
                                    dag.remove_op_node(node)
                                    dag.remove_op_node(next_node)
                                    nodes[index+2] = DAGOpNode(op=Instruction(name='z', num_qubits=1, num_clbits=0, params=[]))
                                    nodes.remove(node)
                                    nodes.remove(next_node)


                if node.op.name in ['s', 'sdg']:

                    if index+1 < len(nodes): 
                        next_node = nodes[index+1]
                        if next_node.op.name in ['s', 'sdg']:
                            if next_node.op.name != node.op.name:
                                dag.remove_op_node(node)
                                dag.remove_op_node(next_node)
                                nodes.remove(node)
                                nodes.remove(next_node)

                            elif next_node.op.name == node.op.name:
                                dag.remove_op_node(node)
                                nodes.remove(node)
                                replacement = QuantumCircuit(1)
                                replacement.z(0)
                                dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))
                                nodes[index+1] = DAGOpNode(op=Instruction(name='z', num_qubits=1, num_clbits=0, params=[]))
                
        return dag





def reduce_circuit_depth(circuit: QuantumCircuit):
    
    """
    Iterative method for circuit reduction.
    
    circuit:
        a QuantumCircuit object that is to be reduced
        
    Returns:
        reduced_circuit:
            the reduced circuit
    """
    circuit_size = circuit.size()
    reduced_circuit = circuit.copy()
    
    while True:
        reduced_circuit = GateReduction()(reduced_circuit) 
        if circuit_size == reduced_circuit.size():
            break
        else:
            circuit_size = reduced_circuit.size()

    return reduced_circuit