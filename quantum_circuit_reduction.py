'''
(C) Renata Wong

This code reduces the number of gates in a quantum circuit according to the following rules:
XX = YY = ZZ = HH = I, Sdg x S = S x Sdg = I, CX x CX = II, HZH = X, HXH = Z, SS = Sdg x Sdg = Z
'''

from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.transpiler import TransformationPass


class GateReduction(TransformationPass):
    
    """
    A transpiler pass to reduce gate number in a circuit.
    """

    def run(self, dag):

        # iterate over all operations in a circuit
        nodes = dag.op_nodes()
        num_nodes = len(nodes)
        
        for index, node in enumerate(nodes):
            
            if node.op.name in ['x', 'y', 'z', 'h', 'cx']:
                
                if index+1 < num_nodes:
                    next_node = nodes[index+1]
                    if next_node.op.name == node.op.name:
                        if node.op.name == 'cx':
                            if node.qargs == next_node.qargs:
                                replacement = QuantumCircuit(2)
                                dag.substitute_node_with_dag(node, circuit_to_dag(replacement))
                                dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))

                        else:
                            replacement = QuantumCircuit(1)
                            dag.substitute_node_with_dag(node, circuit_to_dag(replacement))
                            dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))
                        
                    if node.op.name == 'h' and next_node.op.name == 'z':
                        third_node = nodes[index+2]
                        if third_node.op.name == 'h':
                            replacement = QuantumCircuit(1)
                            dag.substitute_node_with_dag(node, circuit_to_dag(replacement))
                            dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))
                            replacement.x(0)
                            dag.substitute_node_with_dag(third_node, circuit_to_dag(replacement))
                        
                    if node.op.name == 'h' and next_node.op.name == 'x':
                        third_node = nodes[index+2]
                        if third_node.op.name == 'h':
                            replacement = QuantumCircuit(1)
                            dag.substitute_node_with_dag(node, circuit_to_dag(replacement))
                            dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))
                            replacement.z(0)
                            dag.substitute_node_with_dag(third_node, circuit_to_dag(replacement))

                        
            if node.op.name in ['s', 'sdg']:
                
                if index+1 < num_nodes:
                    next_node = nodes[index+1]
                    if next_node.op.name in ['s', 'sdg'] and next_node.op.name != node.op.name:
                        replacement = QuantumCircuit(1)
                        # replace the node with our new decomposition
                        dag.substitute_node_with_dag(node, circuit_to_dag(replacement))
                        dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))
                        
                    if next_node.op.name in ['s', 'sdg'] and next_node.op.name == node.op.name:
                        replacement = QuantumCircuit(1)
                        replacement.z(0)
                        # replace the node with our new decomposition
                        dag.substitute_node_with_dag(node, circuit_to_dag(replacement))
                        dag.substitute_node_with_dag(next_node, circuit_to_dag(replacement))
        
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
    
    qc_gate_number = circuit.depth()
    
    while True:
        reduced_circuit = GateReduction()(circuit)
        reduced_gate_number = reduced_circuit.depth()

        if qc_gate_number == reduced_gate_number:
            break
        else:
            qc_gate_number = reduced_gate_number
        
    return reduced_circuit
        