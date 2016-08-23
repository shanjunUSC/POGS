###### modeling_structure.py ######
#!/usr/bin/env python
##
# Copyright (C) 2016 University of Southern California and
#                          Hanjun Shin
# 
# Authors: Hanjun Shin
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Pipeline description documentation.

ModelingStructureFlow Arguments:
	Required Arguments:
		-i, --input_config 
"""
import argparse
import sys
import os
from subprocess import call
import json
import string

from pyflow_alab.pyflow import WorkflowRunner
#from pyflow import lister

from workflows.utils.args import add_pyflow_args
from workflows.utils.args import default_pyflow_args
from workflows.utils.args import extend_pyflow_docstring
from workflows.modeling.Astep_flow import AStepFlow
from workflows.modeling.Mstep_flow import MStepFlow
from workflows.modeling.ComputeViolationFlow import ComputeViolationFlow

#from workflows.utils.sys_utils import ensure_file_exists
#from workflows.config import SiteConfig

__version__ = "0.0.1"
__author__  = "Hanjun Shin"
__credits__ = ["Nan Hua"]
__license__ = "GPL"
__email__   = "nhua@usc.edu"

class ModelingStructureFlow(WorkflowRunner):
	def __init__(self, input_config):#sys_config, input, output_dir, freq_list, nstruct):
		self.input_config = input_config
		# self.sys_config = sys_config
		# self.input = input
		# self.output_dir = output_dir
		# self.freq_list = freq_list.strip('[|]').split(',')
		# self.nstruct = nstruct
		
	# input validation
		#ensure_file_exists(self.bam)

	def workflow(self):
		###############################################################################
		# input_config file check up
		###############################################################################
		if type(self.input_config) == str :
			if not (os.path.exists(self.input_config) and os.access(self.input_config, os.R_OK) ):
				raise Exception('Cannot Find or Access input_config file %s' % self.input_config)
			with open(self.input_config, 'r') as data_file: 
				self.input_config = json.load(data_file)
		
		if not self.input_config.has_key('source_dir') :
			raise Exception('Input config error, it does not have source_dir ')		
					
		if not self.input_config.has_key('modeling_parameters') :
			raise Exception('%s : Input config error, it does not have modeling_parameters' % os.path.name(__file__))
		else :
			if not self.input_config['modeling_parameters'].has_key('probMat') :
				raise Exception('%s : Input config error, it does not have probMat' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('probability_list') :
				raise Exception('%s : Input config error, it does not have probability_list' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('num_of_structures') :
				raise Exception('%s : Input config error, it does not have num_of_structures' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('max_iter_per_prob') :
				raise Exception('%s : Input config error, it does not have max_iter_per_prob' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('violation_cutoff') :
				raise Exception('%s : Input config error, it does not have violation_cutoff' % os.path.name(__file__))
				
		input = self.input_config['modeling_parameters']['probMat']
		freq_list = self.input_config['modeling_parameters']['probability_list']
		nstruct = self.input_config['modeling_parameters']['num_of_structures']
		max_iter_per_prob = self.input_config['modeling_parameters']['max_iter_per_prob']
		violation_cutoff = self.input_config['modeling_parameters']['violation_cutoff']
		
		#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
		
		last_freq = freq_list[0].strip()
		last_actDist = None
			
		struct_dir = "%s/structure" % self.input_config['output_dir']
		actDist_dir = "%s/actDist" % self.input_config['output_dir']
		
		call(["mkdir", "-p", struct_dir])
		call(["mkdir", "-p", actDist_dir])
				
		compute_violation_task = None
		astep_task = None
		actDist = None
		
		for freq in freq_list:
			newFreq = freq.strip()
			iter_count = 0
		
			while (iter_count < max_iter_per_prob) :
				###############################################################################
				# Astep Flow
				# If violation.json file does not exist, skipped!
				###############################################################################
				a_task_config = self.input_config
				actDist = ""
				
				violation_file = "%s/violation.json" % struct_dir
				if os.path.isfile( violation_file ) :
					data = {}
					with open(violation_file, 'r') as file:
						data = json.load(file)
						
					if not data.has_key( newFreq ) :
						if data.has_key( "pLast" ) : 
							last_freq = data["pLast"]				
	
					#if data.has_key( "pLast" ) :
					#	last_freq = data[ "pLast" ]
					#else :
					#	raise Exception("Cannot find last probability ")
					
					#if data.has_key("pLastActDist") :
					#	last_actDist = "%s/%s" %(actDist_dir, data[ "pLastActDist"])
					#else :
					#	raise Exception("Cannot find last actdist")
					
					a_task_config['modeling_parameters'].update({'struct_dir' : struct_dir})
					a_task_config['modeling_parameters'].update({'freq' : newFreq})
					a_task_config['modeling_parameters'].update({'last_freq' : last_freq})
					actDist = "%s/from.%s.to.%s.actDist" % (actDist_dir, last_freq, newFreq)
					a_task_config['modeling_parameters'].update({'actDist' : actDist})
					a_task_config['modeling_parameters'].update({'last_actDist' : last_actDist})\
					
					if not last_freq == newFreq :
						astep_wf = AStepFlow(a_task_config)
						astep_task = "a_%s_to_%s" % (last_freq.replace(".", ""), newFreq.replace(".", ""))
					
						self.addWorkflowTask(astep_task, astep_wf, dependencies=compute_violation_task)
					else :
						astep_task = None
						actDist = None
					
				else :
					astep_task = None
					actDist = None
					
				#if (newFreq == 'p100') :	
				#	astep_task = None
				#	actDist = None
				#else :
				#	self.addWorkflowTask(astep_task, astep_wf, dependencies=compute_violation_task)
				#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
				
				
				###############################################################################
				# Mstep Flow
				###############################################################################
				m_task_config = self.input_config
				m_task_config['modeling_parameters'].update({'struct_dir' : struct_dir})
				m_task_config['modeling_parameters'].update({'freq' : newFreq})
				m_task_config['modeling_parameters'].update({'last_freq' : last_freq})
				m_task_config['modeling_parameters'].update({'last_actDist' : actDist})
					
				mstep_wf = MStepFlow(m_task_config)
				mstep_task = "m_%s_to_%s" % (last_freq.replace(".", ""), newFreq.replace(".", ""))
				self.addWorkflowTask(mstep_task, mstep_wf, dependencies=astep_task)
				#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
				
				#if not self.isTaskComplete(mstep_task) :
				#	self.waitForTasks(mstep_task)
					
				#################################################################################
				# Compute Violation Flow
				#################################################################################
				compute_violation_task_config = m_task_config
				violation_file = "%s/violation.json" % struct_dir
				compute_violation_task_config['modeling_parameters'].update({'violation_file' : violation_file})
				
				compute_violation_wf = ComputeViolationFlow(compute_violation_task_config)
				compute_violation_task = "cv_%s_to_%s" % (last_freq.replace(".", ""), newFreq.replace(".", ""))
				self.addWorkflowTask( compute_violation_task, compute_violation_wf, dependencies = mstep_task)
				
				#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
								
				if not self.isTaskComplete(compute_violation_task) :
					self.waitForTasks(compute_violation_task)
				
				violation_rate = 0
				
				if os.path.isfile( violation_file ) :
					with open(violation_file, 'r') as file:
						data = json.load(file)
						if data.has_key( newFreq ) :
							violation_rate = data[ newFreq ]["violation"]
						else :
							raise Exception("Cannot find violation rate for current prob %s" % newFreq)
						#violation_log = file.readlines()[-1]
						#violation_rate = float( violation_log.split()[-1] )
				
				last_freq = newFreq
				last_actDist = actDist
				
				if violation_rate <= violation_cutoff :
					break
				
				newFreq	= "%s%s" % (freq, string.ascii_lowercase[iter_count])
				
				iter_count = iter_count + 1
			else :
				print "Process Stopped "
				break
		
if __name__ == "__main__":
	parser = argparse.ArgumentParser(usage=extend_pyflow_docstring(__doc__))
	parser.add_argument('-i', '--input_config', type=str, required=True)
	# parser.add_argument('-i', '--input', type=str, required=True)
	# parser.add_argument('-o', '--output_dir', type=str, required=True)
	# parser.add_argument('-f', '--freq_list', type=str, required=True)
	# parser.add_argument('-n', '--nstruct', type=str, required=True)
	# parser.add_argument('--flag', default=False, action="store_true")
	add_pyflow_args(parser)
	args = parser.parse_args()
	
	modeling_structure_wf = ModelingStructureFlow(args.input_config)
	# modeling_structure_wf = ModelingStructureFlow(
			# args.sys_config,
			# args.input,
			# args.output_dir,
			# args.freq_list,
			# args.nstruct
			# )

	sys.exit(modeling_structure_wf.run(**default_pyflow_args(args)))