import os
from os import walk
import yaml
import regex



def parse_function_data(functions,yaml_data,function_type):
	for function_data in yaml_data.get(function_type, []):
		function = {
			'name': function_data['name'],
			'impls_args': []
		}

		for implementation in function_data.get('impls', []):
			args = []
			for arg in implementation.get('args', []):
				arg_info = {'name': arg.get('name', ''), 'value': arg.get('value', '')}
				args.append(arg_info)

			function['impls_args'].append(args)

		functions.append(function)
	return functions

def parse_yaml(file_path):
	with open(file_path, 'r') as file:
		yaml_data = yaml.safe_load(file)
	functions = []
	functions = parse_function_data(functions,yaml_data,'scalar_functions')
	functions = parse_function_data(functions,yaml_data,'aggregate_functions')
	return functions

def get_custom_functions():
	inner_code = ""
	type_set = set()
	custom_extension_folder  = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','substrait','extensions')
	custom_function_paths = next(walk(custom_extension_folder), (None, None, []))[2]
	for custom_function_path in custom_function_paths:
		functions = parse_yaml(os.path.join(custom_extension_folder,custom_function_path))
		for function in functions:
			for impls_args in function["impls_args"]:
				type_str = "{"
				for args in impls_args: 
					type_value = regex.sub(r'<[^>]*>', '', args["value"])
					type_set.add(type_value)
					type_str += f"\"{type_value}\","
				type_str = type_str[:-1]
				type_str += "}"
				function_name = function["name"]
				inner_code += f"\tInsertCustomFunction(\"{function_name}\", {type_str}, \"{custom_function_path}\");\n" 
	print(type_set)
	return inner_code

def write_custom_extension_file(custom_functions):
	file_path  = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','src','custom_extensions_generated.cpp')
	header = '''#include "custom_extensions/custom_extensions.hpp"

//! This class is auto-generated by scripts/geenrate_extension_initializer.py
//! It depends on substrait/extensions yaml files
namespace duckdb{

void SubstraitCustomFunctions::Initialize(){
	'''
	footer = '''}

} // namespace duckdb'''

	# Open the file in write mode
	with open(file_path, 'w') as file:
	# Write new content to the file
		file.write(header)
		file.write(custom_functions)
		file.write(footer)

functions = get_custom_functions()
write_custom_extension_file(functions)