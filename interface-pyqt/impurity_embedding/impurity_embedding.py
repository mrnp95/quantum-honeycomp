#!/usr/bin/python

from __future__ import print_function

import sys
import os

qhroot = os.path.dirname(os.path.realpath(__file__))+"/../../"
sys.path.append(qhroot+"/pysrc/") # python libraries


from interfacetk import qtwrap # import the library with simple wrappaers to qt4
get = qtwrap.get  # get the value of a certain variable
getbox = qtwrap.getbox  # get the value of a certain variable
window = qtwrap.main() # this is the main interface



from interfacetk.qh_interface import * # import all the libraries needed
from interfacetk import common # common routines for all the geometries

common.initialize(qtwrap) # do several common initializations

qtwrap.set_combobox("scf_initialization",meanfield.spinful_guesses)
qtwrap.set_combobox("bands_color",operators.operator_list)


def get_geometry(modify=True):
  """ Create a 0d island"""
  lattice_name = getbox("lattice") # get the option
  if lattice_name=="Honeycomb":
    geometry_builder = geometry.honeycomb_lattice
  elif lattice_name=="Honeycomb 4 sites":
    geometry_builder = geometry.honeycomb_lattice_square_cell
  elif lattice_name=="Square":
    geometry_builder = geometry.square_lattice
  elif lattice_name=="Single square":
    geometry_builder = geometry.single_square_lattice
  elif lattice_name=="Kagome":
    geometry_builder = geometry.kagome_lattice
  elif lattice_name=="Lieb":
    geometry_builder = geometry.lieb_lattice
  elif lattice_name=="Triangular":
    geometry_builder = geometry.triangular_lattice
  elif lattice_name=="Triangular tripartite":
    geometry_builder = lambda: geometry.triangular_lattice(n=3)
  elif lattice_name=="Honeycomb 6 sites":
    geometry_builder = lambda: geometry.honeycomb_lattice(n=3)
  else: raise
  g = geometry_builder() # call the geometry
  nsuper = int(get("nsuper"))
  g = g.supercell(nsuper)
  if modify: g = modify_geometry(g) # modify the geometry
  return g





def select_atoms_removal():
  g = get_geometry(modify=False) # get the unmodified geometry
  g.write() # write geometry
  execute_script("qh-remove-atoms-geometry") # remove the file


def modify_geometry(g):
  """Modify the geometry according to the interface"""
  if qtwrap.is_checked("remove_selected"): # remove some atoms
      try:
        inds = np.array(np.genfromtxt("REMOVE_ATOMS.INFO",dtype=np.int))
        if inds.shape==(): inds = [inds]
      except: inds = [] # Nothing
      print(inds)
      g = sculpt.remove(g,inds) # remove those atoms
  if qtwrap.is_checked("remove_single_bonded"): # remove single bonds
      g = sculpt.remove_unibonded(g,iterative=True)
#  g.save()
  return g # return geometry











def initialize():
  """ Initialize the calculation"""
  g = get_geometry() # get the geometry
  h = g.get_hamiltonian(has_spin=False)
#  h.add_zeeman([get("Bx"),get("By"),get("Bz")]) # Zeeman fields
  h.add_sublattice_imbalance(get("mAB"))  # sublattice imbalance
#  h.add_rashba(get("rashba"))  # Rashba field
#  h.add_antiferromagnetism(get("mAF"))  # AF order
  h.shift_fermi(get("fermi")) # shift fermi energy
#  h.add_kane_mele(get("kanemele")) # intrinsic SOC
#  h.add_haldane(get("haldane")) # intrinsic SOC
  h.add_antihaldane(get("antihaldane")) 
#  h.add_anti_kane_mele(get("antikanemele")) 
#  if abs(get("swave"))>0.0: 
#      h = h.get_multicell()
#      special_pairing(h)
  return h



def pickup_hamiltonian():
    return initialize()


def show_structure():
  """Show the lattice of the system"""
  g = get_geometry() # get the geometry
  nsuper = int(get("nsuper_struct"))
  g = g.supercell(nsuper)
  g.write()
#  execute_script("qh-light-structure POSITIONS.OUT")
  execute_script("qh-structure-bond --input POSITIONS.OUT")
#  execute_script("qh-structure  ")





def show_structure_3d():
    """Show the lattice of the system"""
    g = get_geometry() # get the geometry
    nsuper = int(get("nsuper_struct"))
    g = g.supercell(nsuper)
    g.write()
    execute_script("qh-structure3d POSITIONS.OUT")


def show_embedding_ldos():
    h = pickup_hamiltonian()
    vintra = h.intra.copy() ; vintra[0,0] = get("impurity_potential")
    eb = embedding.Embedding(h,m=vintra)
    e = get("energy_embedding_ldos") # energy
    delta = get("delta_embedding_ldos") # energy
    ns = int(get("ncells_embedding_ldos"))
    (x,y,d) = eb.ldos(nsuper=ns,e=e,delta=delta)
    np.savetxt("LDOS.OUT",np.array([x,y,d]).T)
    execute_script("qh-ldos --input LDOS.OUT")
#    execute_script("qh-interpolate --input LDOS.OUT --dx -2 --dy -2 --smooth 1.0")
#    execute_script("qh-ldos --input LDOS.OUT-interpolated ")

inipath = os.getcwd() # get the initial directory

save_results = lambda: save_outputs(inipath,tmppath) # function to save

# create signals
signals = dict()
signals["show_structure"] = show_structure  # show bandstructure
signals["select_atoms_removal"] = select_atoms_removal
signals["show_embedding_ldos"] = show_embedding_ldos
signals["save_results"] = save_results





window.connect_clicks(signals)
folder = create_folder()
tmppath = os.getcwd() # get the initial directory
window.run()
