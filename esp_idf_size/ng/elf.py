# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import struct
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple, Union

# Dwarf5: https://dwarfstd.org/doc/DWARF5.pdf

# https://sourceware.org/git/?p=binutils-gdb.git;a=blob;f=include/dwarf2.def
DW_TAG_padding = 0x00
DW_TAG_array_type = 0x01
DW_TAG_class_type = 0x02
DW_TAG_entry_point = 0x03
DW_TAG_enumeration_type = 0x04
DW_TAG_formal_parameter = 0x05
DW_TAG_imported_declaration = 0x08
DW_TAG_label = 0x0a
DW_TAG_lexical_block = 0x0b
DW_TAG_member = 0x0d
DW_TAG_pointer_type = 0x0f
DW_TAG_reference_type = 0x10
DW_TAG_compile_unit = 0x11
DW_TAG_string_type = 0x12
DW_TAG_structure_type = 0x13
DW_TAG_subroutine_type = 0x15
DW_TAG_typedef = 0x16
DW_TAG_union_type = 0x17
DW_TAG_unspecified_parameters = 0x18
DW_TAG_variant = 0x19
DW_TAG_common_block = 0x1a
DW_TAG_common_inclusion = 0x1b
DW_TAG_inheritance = 0x1c
DW_TAG_inlined_subroutine = 0x1d
DW_TAG_module = 0x1e
DW_TAG_ptr_to_member_type = 0x1f
DW_TAG_set_type = 0x20
DW_TAG_subrange_type = 0x21
DW_TAG_with_stmt = 0x22
DW_TAG_access_declaration = 0x23
DW_TAG_base_type = 0x24
DW_TAG_catch_block = 0x25
DW_TAG_const_type = 0x26
DW_TAG_constant = 0x27
DW_TAG_enumerator = 0x28
DW_TAG_file_type = 0x29
DW_TAG_friend = 0x2a
DW_TAG_namelist = 0x2b
DW_TAG_namelist_item = 0x2c
DW_TAG_packed_type = 0x2d
DW_TAG_subprogram = 0x2e
DW_TAG_template_type_param = 0x2f
DW_TAG_template_value_param = 0x30
DW_TAG_thrown_type = 0x31
DW_TAG_try_block = 0x32
DW_TAG_variant_part = 0x33
DW_TAG_variable = 0x34
DW_TAG_volatile_type = 0x35
DW_TAG_dwarf_procedure = 0x36
DW_TAG_restrict_type = 0x37
DW_TAG_interface_type = 0x38
DW_TAG_namespace = 0x39
DW_TAG_imported_module = 0x3a
DW_TAG_unspecified_type = 0x3b
DW_TAG_partial_unit = 0x3c
DW_TAG_imported_unit = 0x3d
DW_TAG_condition = 0x3f
DW_TAG_shared_type = 0x40
DW_TAG_type_unit = 0x41
DW_TAG_rvalue_reference_type = 0x42
DW_TAG_template_alias = 0x43
DW_TAG_coarray_type = 0x44
DW_TAG_generic_subrange = 0x45
DW_TAG_dynamic_type = 0x46
DW_TAG_atomic_type = 0x47
DW_TAG_call_site = 0x48
DW_TAG_call_site_parameter = 0x49
DW_TAG_skeleton_unit = 0x4a
DW_TAG_immutable_type = 0x4b
DW_TAG_lo_user = 0x4080
DW_TAG_hi_user = 0xffff
DW_TAG_MIPS_loop = 0x4081
DW_TAG_HP_array_descriptor = 0x4090
DW_TAG_HP_Bliss_field = 0x4091
DW_TAG_HP_Bliss_field_set = 0x4092
DW_TAG_format_label = 0x4101
DW_TAG_function_template = 0x4102
DW_TAG_class_template = 0x4103
DW_TAG_GNU_BINCL = 0x4104
DW_TAG_GNU_EINCL = 0x4105
DW_TAG_GNU_template_template_param = 0x4106
DW_TAG_GNU_template_parameter_pack = 0x4107
DW_TAG_GNU_formal_parameter_pack = 0x4108
DW_TAG_GNU_call_site = 0x4109
DW_TAG_GNU_call_site_parameter = 0x410a
DW_TAG_upc_shared_type = 0x8765
DW_TAG_upc_strict_type = 0x8766
DW_TAG_upc_relaxed_type = 0x8767
DW_TAG_PGI_kanji_type = 0xA000
DW_TAG_PGI_interface_block = 0xA020

DW_TAG_NAME_MAP: Dict[int, str] = {
    0x00: 'DW_TAG_padding',
    0x01: 'DW_TAG_array_type',
    0x02: 'DW_TAG_class_type',
    0x03: 'DW_TAG_entry_point',
    0x04: 'DW_TAG_enumeration_type',
    0x05: 'DW_TAG_formal_parameter',
    0x08: 'DW_TAG_imported_declaration',
    0x0a: 'DW_TAG_label',
    0x0b: 'DW_TAG_lexical_block',
    0x0d: 'DW_TAG_member',
    0x0f: 'DW_TAG_pointer_type',
    0x10: 'DW_TAG_reference_type',
    0x11: 'DW_TAG_compile_unit',
    0x12: 'DW_TAG_string_type',
    0x13: 'DW_TAG_structure_type',
    0x15: 'DW_TAG_subroutine_type',
    0x16: 'DW_TAG_typedef',
    0x17: 'DW_TAG_union_type',
    0x18: 'DW_TAG_unspecified_parameters',
    0x19: 'DW_TAG_variant',
    0x1a: 'DW_TAG_common_block',
    0x1b: 'DW_TAG_common_inclusion',
    0x1c: 'DW_TAG_inheritance',
    0x1d: 'DW_TAG_inlined_subroutine',
    0x1e: 'DW_TAG_module',
    0x1f: 'DW_TAG_ptr_to_member_type',
    0x20: 'DW_TAG_set_type',
    0x21: 'DW_TAG_subrange_type',
    0x22: 'DW_TAG_with_stmt',
    0x23: 'DW_TAG_access_declaration',
    0x24: 'DW_TAG_base_type',
    0x25: 'DW_TAG_catch_block',
    0x26: 'DW_TAG_const_type',
    0x27: 'DW_TAG_constant',
    0x28: 'DW_TAG_enumerator',
    0x29: 'DW_TAG_file_type',
    0x2a: 'DW_TAG_friend',
    0x2b: 'DW_TAG_namelist',
    0x2c: 'DW_TAG_namelist_item',
    0x2d: 'DW_TAG_packed_type',
    0x2e: 'DW_TAG_subprogram',
    0x2f: 'DW_TAG_template_type_param',
    0x30: 'DW_TAG_template_value_param',
    0x31: 'DW_TAG_thrown_type',
    0x32: 'DW_TAG_try_block',
    0x33: 'DW_TAG_variant_part',
    0x34: 'DW_TAG_variable',
    0x35: 'DW_TAG_volatile_type',
    0x36: 'DW_TAG_dwarf_procedure',
    0x37: 'DW_TAG_restrict_type',
    0x38: 'DW_TAG_interface_type',
    0x39: 'DW_TAG_namespace',
    0x3a: 'DW_TAG_imported_module',
    0x3b: 'DW_TAG_unspecified_type',
    0x3c: 'DW_TAG_partial_unit',
    0x3d: 'DW_TAG_imported_unit',
    0x3f: 'DW_TAG_condition',
    0x40: 'DW_TAG_shared_type',
    0x41: 'DW_TAG_type_unit',
    0x42: 'DW_TAG_rvalue_reference_type',
    0x43: 'DW_TAG_template_alias',
    0x44: 'DW_TAG_coarray_type',
    0x45: 'DW_TAG_generic_subrange',
    0x46: 'DW_TAG_dynamic_type',
    0x47: 'DW_TAG_atomic_type',
    0x48: 'DW_TAG_call_site',
    0x49: 'DW_TAG_call_site_parameter',
    0x4a: 'DW_TAG_skeleton_unit',
    0x4b: 'DW_TAG_immutable_type',
    0x4080: 'DW_TAG_lo_user',
    0xffff: 'DW_TAG_hi_user',
    0x4081: 'DW_TAG_MIPS_loop',
    0x4090: 'DW_TAG_HP_array_descriptor',
    0x4091: 'DW_TAG_HP_Bliss_field',
    0x4092: 'DW_TAG_HP_Bliss_field_set',
    0x4101: 'DW_TAG_format_label',
    0x4102: 'DW_TAG_function_template',
    0x4103: 'DW_TAG_class_template',
    0x4104: 'DW_TAG_GNU_BINCL',
    0x4105: 'DW_TAG_GNU_EINCL',
    0x4106: 'DW_TAG_GNU_template_template_param',
    0x4107: 'DW_TAG_GNU_template_parameter_pack',
    0x4108: 'DW_TAG_GNU_formal_parameter_pack',
    0x4109: 'DW_TAG_GNU_call_site',
    0x410a: 'DW_TAG_GNU_call_site_parameter',
    0x8765: 'DW_TAG_upc_shared_type',
    0x8766: 'DW_TAG_upc_strict_type',
    0x8767: 'DW_TAG_upc_relaxed_type',
    0xA000: 'DW_TAG_PGI_kanji_type',
    0xA020: 'DW_TAG_PGI_interface_block',
}


def get_tag_name(tag: int) -> str:
    return DW_TAG_NAME_MAP[tag] if tag in DW_TAG_NAME_MAP else f'UNKNOWN {tag}'


DW_AT_end = 0x00
DW_AT_sibling = 0x01
DW_AT_location = 0x02
DW_AT_name = 0x03
DW_AT_ordering = 0x09
DW_AT_subscr_data = 0x0a
DW_AT_byte_size = 0x0b
DW_AT_bit_offset = 0x0c
DW_AT_bit_size = 0x0d
DW_AT_element_list = 0x0f
DW_AT_stmt_list = 0x10
DW_AT_low_pc = 0x11
DW_AT_high_pc = 0x12
DW_AT_language = 0x13
DW_AT_member = 0x14
DW_AT_discr = 0x15
DW_AT_discr_value = 0x16
DW_AT_visibility = 0x17
DW_AT_import = 0x18
DW_AT_string_length = 0x19
DW_AT_common_reference = 0x1a
DW_AT_comp_dir = 0x1b
DW_AT_const_value = 0x1c
DW_AT_containing_type = 0x1d
DW_AT_default_value = 0x1e
DW_AT_inline = 0x20
DW_AT_is_optional = 0x21
DW_AT_lower_bound = 0x22
DW_AT_producer = 0x25
DW_AT_prototyped = 0x27
DW_AT_return_addr = 0x2a
DW_AT_start_scope = 0x2c
DW_AT_bit_stride = 0x2e
DW_AT_upper_bound = 0x2f
DW_AT_abstract_origin = 0x31
DW_AT_accessibility = 0x32
DW_AT_address_class = 0x33
DW_AT_artificial = 0x34
DW_AT_base_types = 0x35
DW_AT_calling_convention = 0x36
DW_AT_count = 0x37
DW_AT_data_member_location = 0x38
DW_AT_decl_column = 0x39
DW_AT_decl_file = 0x3a
DW_AT_decl_line = 0x3b
DW_AT_declaration = 0x3c
DW_AT_discr_list = 0x3d
DW_AT_encoding = 0x3e
DW_AT_external = 0x3f
DW_AT_frame_base = 0x40
DW_AT_friend = 0x41
DW_AT_identifier_case = 0x42
DW_AT_macro_info = 0x43
DW_AT_namelist_item = 0x44
DW_AT_priority = 0x45
DW_AT_segment = 0x46
DW_AT_specification = 0x47
DW_AT_static_link = 0x48
DW_AT_type = 0x49
DW_AT_use_location = 0x4a
DW_AT_variable_parameter = 0x4b
DW_AT_virtuality = 0x4c
DW_AT_vtable_elem_location = 0x4d
DW_AT_allocated = 0x4e
DW_AT_associated = 0x4f
DW_AT_data_location = 0x50
DW_AT_byte_stride = 0x51
DW_AT_entry_pc = 0x52
DW_AT_use_UTF8 = 0x53
DW_AT_extension = 0x54
DW_AT_ranges = 0x55
DW_AT_trampoline = 0x56
DW_AT_call_column = 0x57
DW_AT_call_file = 0x58
DW_AT_call_line = 0x59
DW_AT_description = 0x5a
DW_AT_binary_scale = 0x5b
DW_AT_decimal_scale = 0x5c
DW_AT_small = 0x5d
DW_AT_decimal_sign = 0x5e
DW_AT_digit_count = 0x5f
DW_AT_picture_string = 0x60
DW_AT_mutable = 0x61
DW_AT_threads_scaled = 0x62
DW_AT_explicit = 0x63
DW_AT_object_pointer = 0x64
DW_AT_endianity = 0x65
DW_AT_elemental = 0x66
DW_AT_pure = 0x67
DW_AT_recursive = 0x68
DW_AT_signature = 0x69
DW_AT_main_subprogram = 0x6a
DW_AT_data_bit_offset = 0x6b
DW_AT_const_expr = 0x6c
DW_AT_enum_class = 0x6d
DW_AT_linkage_name = 0x6e
DW_AT_string_length_bit_size = 0x6f
DW_AT_string_length_byte_size = 0x70
DW_AT_rank = 0x71
DW_AT_str_offsets_base = 0x72
DW_AT_addr_base = 0x73
DW_AT_rnglists_base = 0x74
DW_AT_dwo_name = 0x76
DW_AT_reference = 0x77
DW_AT_rvalue_reference = 0x78
DW_AT_macros = 0x79
DW_AT_call_all_calls = 0x7a
DW_AT_call_all_source_calls = 0x7b
DW_AT_call_all_tail_calls = 0x7c
DW_AT_call_return_pc = 0x7d
DW_AT_call_value = 0x7e
DW_AT_call_origin = 0x7f
DW_AT_call_parameter = 0x80
DW_AT_call_pc = 0x81
DW_AT_call_tail_call = 0x82
DW_AT_call_target = 0x83
DW_AT_call_target_clobbered = 0x84
DW_AT_call_data_location = 0x85
DW_AT_call_data_value = 0x86
DW_AT_noreturn = 0x87
DW_AT_alignment = 0x88
DW_AT_export_symbols = 0x89
DW_AT_deleted = 0x8a
DW_AT_defaulted = 0x8b
DW_AT_loclists_base = 0x8c
DW_AT_lo_user = 0x2000
DW_AT_hi_user = 0x3fff
DW_AT_MIPS_fde = 0x2001
DW_AT_MIPS_loop_begin = 0x2002
DW_AT_MIPS_tail_loop_begin = 0x2003
DW_AT_MIPS_epilog_begin = 0x2004
DW_AT_MIPS_loop_unroll_factor = 0x2005
DW_AT_MIPS_software_pipeline_depth = 0x2006
DW_AT_MIPS_linkage_name = 0x2007
DW_AT_MIPS_stride = 0x2008
DW_AT_MIPS_abstract_name = 0x2009
DW_AT_MIPS_clone_origin = 0x200a
DW_AT_MIPS_has_inlines = 0x200b
DW_AT_HP_block_index = 0x2000
DW_AT_HP_unmodifiable = 0x2001
DW_AT_HP_prologue = 0x2005
DW_AT_HP_epilogue = 0x2008
DW_AT_HP_actuals_stmt_list = 0x2010
DW_AT_HP_proc_per_section = 0x2011
DW_AT_HP_raw_data_ptr = 0x2012
DW_AT_HP_pass_by_reference = 0x2013
DW_AT_HP_opt_level = 0x2014
DW_AT_HP_prof_version_id = 0x2015
DW_AT_HP_opt_flags = 0x2016
DW_AT_HP_cold_region_low_pc = 0x2017
DW_AT_HP_cold_region_high_pc = 0x2018
DW_AT_HP_all_variables_modifiable = 0x2019
DW_AT_HP_linkage_name = 0x201a
DW_AT_HP_prof_flags = 0x201b
DW_AT_HP_unit_name = 0x201f
DW_AT_HP_unit_size = 0x2020
DW_AT_HP_widened_byte_size = 0x2021
DW_AT_HP_definition_points = 0x2022
DW_AT_HP_default_location = 0x2023
DW_AT_HP_is_result_param = 0x2029
DW_AT_sf_names = 0x2101
DW_AT_src_info = 0x2102
DW_AT_mac_info = 0x2103
DW_AT_src_coords = 0x2104
DW_AT_body_begin = 0x2105
DW_AT_body_end = 0x2106
DW_AT_GNU_vector = 0x2107
DW_AT_GNU_guarded_by = 0x2108
DW_AT_GNU_pt_guarded_by = 0x2109
DW_AT_GNU_guarded = 0x210a
DW_AT_GNU_pt_guarded = 0x210b
DW_AT_GNU_locks_excluded = 0x210c
DW_AT_GNU_exclusive_locks_required = 0x210d
DW_AT_GNU_shared_locks_required = 0x210e
DW_AT_GNU_odr_signature = 0x210f
DW_AT_GNU_template_name = 0x2110
DW_AT_GNU_call_site_value = 0x2111
DW_AT_GNU_call_site_data_value = 0x2112
DW_AT_GNU_call_site_target = 0x2113
DW_AT_GNU_call_site_target_clobbered = 0x2114
DW_AT_GNU_tail_call = 0x2115
DW_AT_GNU_all_tail_call_sites = 0x2116
DW_AT_GNU_all_call_sites = 0x2117
DW_AT_GNU_all_source_call_sites = 0x2118
DW_AT_GNU_macros = 0x2119
DW_AT_GNU_deleted = 0x211a
DW_AT_GNU_dwo_name = 0x2130
DW_AT_GNU_dwo_id = 0x2131
DW_AT_GNU_ranges_base = 0x2132
DW_AT_GNU_addr_base = 0x2133
DW_AT_GNU_pubnames = 0x2134
DW_AT_GNU_pubtypes = 0x2135
DW_AT_GNU_discriminator = 0x2136
DW_AT_GNU_locviews = 0x2137
DW_AT_GNU_entry_view = 0x2138
DW_AT_VMS_rtnbeg_pd_address = 0x2201
DW_AT_use_GNAT_descriptive_type = 0x2301
DW_AT_GNAT_descriptive_type = 0x2302
DW_AT_upc_threads_scaled = 0x3210
DW_AT_PGI_lbase = 0x3a00
DW_AT_PGI_soffset = 0x3a01
DW_AT_PGI_lstride = 0x3a02
DW_AT_APPLE_optimized = 0x3fe1
DW_AT_APPLE_flags = 0x3fe2
DW_AT_APPLE_isa = 0x3fe3
DW_AT_APPLE_block = 0x3fe4
DW_AT_APPLE_major_runtime_vers = 0x3fe5
DW_AT_APPLE_runtime_class = 0x3fe6
DW_AT_APPLE_omit_frame_ptr = 0x3fe7
DW_AT_APPLE_property_name = 0x3fe8
DW_AT_APPLE_property_getter = 0x3fe9
DW_AT_APPLE_property_setter = 0x3fea
DW_AT_APPLE_property_attribute = 0x3feb
DW_AT_APPLE_objc_complete_type = 0x3fec
DW_AT_APPLE_property = 0x3fed

DW_AT_NAME_MAP: Dict[int, str] = {
    0x00: 'DW_AT_end',
    0x01: 'DW_AT_sibling',
    0x02: 'DW_AT_location',
    0x03: 'DW_AT_name',
    0x09: 'DW_AT_ordering',
    0x0a: 'DW_AT_subscr_data',
    0x0b: 'DW_AT_byte_size',
    0x0c: 'DW_AT_bit_offset',
    0x0d: 'DW_AT_bit_size',
    0x0f: 'DW_AT_element_list',
    0x10: 'DW_AT_stmt_list',
    0x11: 'DW_AT_low_pc',
    0x12: 'DW_AT_high_pc',
    0x13: 'DW_AT_language',
    0x14: 'DW_AT_member',
    0x15: 'DW_AT_discr',
    0x16: 'DW_AT_discr_value',
    0x17: 'DW_AT_visibility',
    0x18: 'DW_AT_import',
    0x19: 'DW_AT_string_length',
    0x1a: 'DW_AT_common_reference',
    0x1b: 'DW_AT_comp_dir',
    0x1c: 'DW_AT_const_value',
    0x1d: 'DW_AT_containing_type',
    0x1e: 'DW_AT_default_value',
    0x20: 'DW_AT_inline',
    0x21: 'DW_AT_is_optional',
    0x22: 'DW_AT_lower_bound',
    0x25: 'DW_AT_producer',
    0x27: 'DW_AT_prototyped',
    0x2a: 'DW_AT_return_addr',
    0x2c: 'DW_AT_start_scope',
    0x2e: 'DW_AT_bit_stride',
    0x2f: 'DW_AT_upper_bound',
    0x31: 'DW_AT_abstract_origin',
    0x32: 'DW_AT_accessibility',
    0x33: 'DW_AT_address_class',
    0x34: 'DW_AT_artificial',
    0x35: 'DW_AT_base_types',
    0x36: 'DW_AT_calling_convention',
    0x37: 'DW_AT_count',
    0x38: 'DW_AT_data_member_location',
    0x39: 'DW_AT_decl_column',
    0x3a: 'DW_AT_decl_file',
    0x3b: 'DW_AT_decl_line',
    0x3c: 'DW_AT_declaration',
    0x3d: 'DW_AT_discr_list',
    0x3e: 'DW_AT_encoding',
    0x3f: 'DW_AT_external',
    0x40: 'DW_AT_frame_base',
    0x41: 'DW_AT_friend',
    0x42: 'DW_AT_identifier_case',
    0x43: 'DW_AT_macro_info',
    0x44: 'DW_AT_namelist_item',
    0x45: 'DW_AT_priority',
    0x46: 'DW_AT_segment',
    0x47: 'DW_AT_specification',
    0x48: 'DW_AT_static_link',
    0x49: 'DW_AT_type',
    0x4a: 'DW_AT_use_location',
    0x4b: 'DW_AT_variable_parameter',
    0x4c: 'DW_AT_virtuality',
    0x4d: 'DW_AT_vtable_elem_location',
    0x4e: 'DW_AT_allocated',
    0x4f: 'DW_AT_associated',
    0x50: 'DW_AT_data_location',
    0x51: 'DW_AT_byte_stride',
    0x52: 'DW_AT_entry_pc',
    0x53: 'DW_AT_use_UTF8',
    0x54: 'DW_AT_extension',
    0x55: 'DW_AT_ranges',
    0x56: 'DW_AT_trampoline',
    0x57: 'DW_AT_call_column',
    0x58: 'DW_AT_call_file',
    0x59: 'DW_AT_call_line',
    0x5a: 'DW_AT_description',
    0x5b: 'DW_AT_binary_scale',
    0x5c: 'DW_AT_decimal_scale',
    0x5d: 'DW_AT_small',
    0x5e: 'DW_AT_decimal_sign',
    0x5f: 'DW_AT_digit_count',
    0x60: 'DW_AT_picture_string',
    0x61: 'DW_AT_mutable',
    0x62: 'DW_AT_threads_scaled',
    0x63: 'DW_AT_explicit',
    0x64: 'DW_AT_object_pointer',
    0x65: 'DW_AT_endianity',
    0x66: 'DW_AT_elemental',
    0x67: 'DW_AT_pure',
    0x68: 'DW_AT_recursive',
    0x69: 'DW_AT_signature',
    0x6a: 'DW_AT_main_subprogram',
    0x6b: 'DW_AT_data_bit_offset',
    0x6c: 'DW_AT_const_expr',
    0x6d: 'DW_AT_enum_class',
    0x6e: 'DW_AT_linkage_name',
    0x6f: 'DW_AT_string_length_bit_size',
    0x70: 'DW_AT_string_length_byte_size',
    0x71: 'DW_AT_rank',
    0x72: 'DW_AT_str_offsets_base',
    0x73: 'DW_AT_addr_base',
    0x74: 'DW_AT_rnglists_base',
    0x76: 'DW_AT_dwo_name',
    0x77: 'DW_AT_reference',
    0x78: 'DW_AT_rvalue_reference',
    0x79: 'DW_AT_macros',
    0x7a: 'DW_AT_call_all_calls',
    0x7b: 'DW_AT_call_all_source_calls',
    0x7c: 'DW_AT_call_all_tail_calls',
    0x7d: 'DW_AT_call_return_pc',
    0x7e: 'DW_AT_call_value',
    0x7f: 'DW_AT_call_origin',
    0x80: 'DW_AT_call_parameter',
    0x81: 'DW_AT_call_pc',
    0x82: 'DW_AT_call_tail_call',
    0x83: 'DW_AT_call_target',
    0x84: 'DW_AT_call_target_clobbered',
    0x85: 'DW_AT_call_data_location',
    0x86: 'DW_AT_call_data_value',
    0x87: 'DW_AT_noreturn',
    0x88: 'DW_AT_alignment',
    0x89: 'DW_AT_export_symbols',
    0x8a: 'DW_AT_deleted',
    0x8b: 'DW_AT_defaulted',
    0x8c: 'DW_AT_loclists_base',
    0x2000: 'DW_AT_lo_user/DW_AT_HP_block_index',
    0x3fff: 'DW_AT_hi_user',
    0x2001: 'DW_AT_MIPS_fde/DW_AT_HP_unmodifiable',
    0x2002: 'DW_AT_MIPS_loop_begin',
    0x2003: 'DW_AT_MIPS_tail_loop_begin',
    0x2004: 'DW_AT_MIPS_epilog_begin',
    0x2005: 'DW_AT_MIPS_loop_unroll_factor/DW_AT_HP_prologue',
    0x2006: 'DW_AT_MIPS_software_pipeline_depth',
    0x2007: 'DW_AT_MIPS_linkage_name',
    0x2008: 'DW_AT_MIPS_stride/DW_AT_HP_epilogue',
    0x2009: 'DW_AT_MIPS_abstract_name',
    0x200a: 'DW_AT_MIPS_clone_origin',
    0x200b: 'DW_AT_MIPS_has_inlines',
    0x2010: 'DW_AT_HP_actuals_stmt_list',
    0x2011: 'DW_AT_HP_proc_per_section',
    0x2012: 'DW_AT_HP_raw_data_ptr',
    0x2013: 'DW_AT_HP_pass_by_reference',
    0x2014: 'DW_AT_HP_opt_level',
    0x2015: 'DW_AT_HP_prof_version_id',
    0x2016: 'DW_AT_HP_opt_flags',
    0x2017: 'DW_AT_HP_cold_region_low_pc',
    0x2018: 'DW_AT_HP_cold_region_high_pc',
    0x2019: 'DW_AT_HP_all_variables_modifiable',
    0x201a: 'DW_AT_HP_linkage_name',
    0x201b: 'DW_AT_HP_prof_flags',
    0x201f: 'DW_AT_HP_unit_name',
    0x2020: 'DW_AT_HP_unit_size',
    0x2021: 'DW_AT_HP_widened_byte_size',
    0x2022: 'DW_AT_HP_definition_points',
    0x2023: 'DW_AT_HP_default_location',
    0x2029: 'DW_AT_HP_is_result_param',
    0x2101: 'DW_AT_sf_names',
    0x2102: 'DW_AT_src_info',
    0x2103: 'DW_AT_mac_info',
    0x2104: 'DW_AT_src_coords',
    0x2105: 'DW_AT_body_begin',
    0x2106: 'DW_AT_body_end',
    0x2107: 'DW_AT_GNU_vector',
    0x2108: 'DW_AT_GNU_guarded_by',
    0x2109: 'DW_AT_GNU_pt_guarded_by',
    0x210a: 'DW_AT_GNU_guarded',
    0x210b: 'DW_AT_GNU_pt_guarded',
    0x210c: 'DW_AT_GNU_locks_excluded',
    0x210d: 'DW_AT_GNU_exclusive_locks_required',
    0x210e: 'DW_AT_GNU_shared_locks_required',
    0x210f: 'DW_AT_GNU_odr_signature',
    0x2110: 'DW_AT_GNU_template_name',
    0x2111: 'DW_AT_GNU_call_site_value',
    0x2112: 'DW_AT_GNU_call_site_data_value',
    0x2113: 'DW_AT_GNU_call_site_target',
    0x2114: 'DW_AT_GNU_call_site_target_clobbered',
    0x2115: 'DW_AT_GNU_tail_call',
    0x2116: 'DW_AT_GNU_all_tail_call_sites',
    0x2117: 'DW_AT_GNU_all_call_sites',
    0x2118: 'DW_AT_GNU_all_source_call_sites',
    0x2119: 'DW_AT_GNU_macros',
    0x211a: 'DW_AT_GNU_deleted',
    0x2130: 'DW_AT_GNU_dwo_name',
    0x2131: 'DW_AT_GNU_dwo_id',
    0x2132: 'DW_AT_GNU_ranges_base',
    0x2133: 'DW_AT_GNU_addr_base',
    0x2134: 'DW_AT_GNU_pubnames',
    0x2135: 'DW_AT_GNU_pubtypes',
    0x2136: 'DW_AT_GNU_discriminator',
    0x2137: 'DW_AT_GNU_locviews',
    0x2138: 'DW_AT_GNU_entry_view',
    0x2201: 'DW_AT_VMS_rtnbeg_pd_address',
    0x2301: 'DW_AT_use_GNAT_descriptive_type',
    0x2302: 'DW_AT_GNAT_descriptive_type',
    0x3210: 'DW_AT_upc_threads_scaled',
    0x3a00: 'DW_AT_PGI_lbase',
    0x3a01: 'DW_AT_PGI_soffset',
    0x3a02: 'DW_AT_PGI_lstride',
    0x3fe1: 'DW_AT_APPLE_optimized',
    0x3fe2: 'DW_AT_APPLE_flags',
    0x3fe3: 'DW_AT_APPLE_isa',
    0x3fe4: 'DW_AT_APPLE_block',
    0x3fe5: 'DW_AT_APPLE_major_runtime_vers',
    0x3fe6: 'DW_AT_APPLE_runtime_class',
    0x3fe7: 'DW_AT_APPLE_omit_frame_ptr',
    0x3fe8: 'DW_AT_APPLE_property_name',
    0x3fe9: 'DW_AT_APPLE_property_getter',
    0x3fea: 'DW_AT_APPLE_property_setter',
    0x3feb: 'DW_AT_APPLE_property_attribute',
    0x3fec: 'DW_AT_APPLE_objc_complete_type',
    0x3fed: 'DW_AT_APPLE_property',
}


def get_attr_name(attr: int) -> str:
    return DW_AT_NAME_MAP[attr] if attr in DW_AT_NAME_MAP else f'UNKNOWN {attr}'


DW_FORM_end = 0x00
DW_FORM_addr = 0x01
DW_FORM_block2 = 0x03
DW_FORM_block4 = 0x04
DW_FORM_data2 = 0x05
DW_FORM_data4 = 0x06
DW_FORM_data8 = 0x07
DW_FORM_string = 0x08
DW_FORM_block = 0x09
DW_FORM_block1 = 0x0a
DW_FORM_data1 = 0x0b
DW_FORM_flag = 0x0c
DW_FORM_sdata = 0x0d
DW_FORM_strp = 0x0e
DW_FORM_udata = 0x0f
DW_FORM_ref_addr = 0x10
DW_FORM_ref1 = 0x11
DW_FORM_ref2 = 0x12
DW_FORM_ref4 = 0x13
DW_FORM_ref8 = 0x14
DW_FORM_ref_udata = 0x15
DW_FORM_indirect = 0x16
DW_FORM_sec_offset = 0x17
DW_FORM_exprloc = 0x18
DW_FORM_flag_present = 0x19
DW_FORM_ref_sig8 = 0x20
DW_FORM_strx = 0x1a
DW_FORM_addrx = 0x1b
DW_FORM_ref_sup4 = 0x1c
DW_FORM_strp_sup = 0x1d
DW_FORM_data16 = 0x1e
DW_FORM_line_strp = 0x1f
DW_FORM_implicit_const = 0x21
DW_FORM_loclistx = 0x22
DW_FORM_rnglistx = 0x23
DW_FORM_ref_sup8 = 0x24
DW_FORM_strx1 = 0x25
DW_FORM_strx2 = 0x26
DW_FORM_strx3 = 0x27
DW_FORM_strx4 = 0x28
DW_FORM_addrx1 = 0x29
DW_FORM_addrx2 = 0x2a
DW_FORM_addrx3 = 0x2b
DW_FORM_addrx4 = 0x2c
DW_FORM_GNU_addr_index = 0x1f01
DW_FORM_GNU_str_index = 0x1f02
DW_FORM_GNU_ref_alt = 0x1f20
DW_FORM_GNU_strp_alt = 0x1f21

DW_FORM_NAME_MAP: Dict[int, str] = {
    0x00: 'DW_FORM_end',
    0x01: 'DW_FORM_addr',
    0x03: 'DW_FORM_block2',
    0x04: 'DW_FORM_block4',
    0x05: 'DW_FORM_data2',
    0x06: 'DW_FORM_data4',
    0x07: 'DW_FORM_data8',
    0x08: 'DW_FORM_string',
    0x09: 'DW_FORM_block',
    0x0a: 'DW_FORM_block1',
    0x0b: 'DW_FORM_data1',
    0x0c: 'DW_FORM_flag',
    0x0d: 'DW_FORM_sdata',
    0x0e: 'DW_FORM_strp',
    0x0f: 'DW_FORM_udata',
    0x10: 'DW_FORM_ref_addr',
    0x11: 'DW_FORM_ref1',
    0x12: 'DW_FORM_ref2',
    0x13: 'DW_FORM_ref4',
    0x14: 'DW_FORM_ref8',
    0x15: 'DW_FORM_ref_udata',
    0x16: 'DW_FORM_indirect',
    0x17: 'DW_FORM_sec_offset',
    0x18: 'DW_FORM_exprloc',
    0x19: 'DW_FORM_flag_present',
    0x20: 'DW_FORM_ref_sig8',
    0x1a: 'DW_FORM_strx',
    0x1b: 'DW_FORM_addrx',
    0x1c: 'DW_FORM_ref_sup4',
    0x1d: 'DW_FORM_strp_sup',
    0x1e: 'DW_FORM_data16',
    0x1f: 'DW_FORM_line_strp',
    0x21: 'DW_FORM_implicit_const',
    0x22: 'DW_FORM_loclistx',
    0x23: 'DW_FORM_rnglistx',
    0x24: 'DW_FORM_ref_sup8',
    0x25: 'DW_FORM_strx1',
    0x26: 'DW_FORM_strx2',
    0x27: 'DW_FORM_strx3',
    0x28: 'DW_FORM_strx4',
    0x29: 'DW_FORM_addrx1',
    0x2a: 'DW_FORM_addrx2',
    0x2b: 'DW_FORM_addrx3',
    0x2c: 'DW_FORM_addrx4',
    0x1f01: 'DW_FORM_GNU_addr_index',
    0x1f02: 'DW_FORM_GNU_str_index',
    0x1f20: 'DW_FORM_GNU_ref_alt',
    0x1f21: 'DW_FORM_GNU_strp_alt',
}


def get_form_name(form: int) -> str:
    return DW_FORM_NAME_MAP[form] if form in DW_FORM_NAME_MAP else f'UNKNOWN {form}'


DW_OP_addr = 0x03
DW_OP_deref = 0x06
DW_OP_deref = 0x06
DW_OP_const1u = 0x08
DW_OP_const1s = 0x09
DW_OP_const2u = 0x0a
DW_OP_const2s = 0x0b
DW_OP_const4u = 0x0c
DW_OP_const4s = 0x0d
DW_OP_const8u = 0x0e
DW_OP_const8s = 0x0f
DW_OP_constu = 0x10
DW_OP_consts = 0x11
DW_OP_dup = 0x12
DW_OP_drop = 0x13
DW_OP_over = 0x14
DW_OP_pick = 0x15
DW_OP_swap = 0x16
DW_OP_rot = 0x17
DW_OP_xderef = 0x18
DW_OP_abs = 0x19
DW_OP_and = 0x1a
DW_OP_div = 0x1b
DW_OP_minus = 0x1c
DW_OP_mod = 0x1d
DW_OP_mul = 0x1e
DW_OP_neg = 0x1f
DW_OP_not = 0x20
DW_OP_or = 0x21
DW_OP_plus = 0x22
DW_OP_plus_uconst = 0x23
DW_OP_shl = 0x24
DW_OP_shr = 0x25
DW_OP_shra = 0x26
DW_OP_xor = 0x27
DW_OP_bra = 0x28
DW_OP_eq = 0x29
DW_OP_ge = 0x2a
DW_OP_gt = 0x2b
DW_OP_le = 0x2c
DW_OP_lt = 0x2d
DW_OP_ne = 0x2e
DW_OP_skip = 0x2f
DW_OP_lit0 = 0x30
DW_OP_lit1 = 0x31
DW_OP_lit2 = 0x32
DW_OP_lit3 = 0x33
DW_OP_lit4 = 0x34
DW_OP_lit5 = 0x35
DW_OP_lit6 = 0x36
DW_OP_lit7 = 0x37
DW_OP_lit8 = 0x38
DW_OP_lit9 = 0x39
DW_OP_lit10 = 0x3a
DW_OP_lit11 = 0x3b
DW_OP_lit12 = 0x3c
DW_OP_lit13 = 0x3d
DW_OP_lit14 = 0x3e
DW_OP_lit15 = 0x3f
DW_OP_lit16 = 0x40
DW_OP_lit17 = 0x41
DW_OP_lit18 = 0x42
DW_OP_lit19 = 0x43
DW_OP_lit20 = 0x44
DW_OP_lit21 = 0x45
DW_OP_lit22 = 0x46
DW_OP_lit23 = 0x47
DW_OP_lit24 = 0x48
DW_OP_lit25 = 0x49
DW_OP_lit26 = 0x4a
DW_OP_lit27 = 0x4b
DW_OP_lit28 = 0x4c
DW_OP_lit29 = 0x4d
DW_OP_lit30 = 0x4e
DW_OP_lit31 = 0x4f
DW_OP_reg0 = 0x50
DW_OP_reg1 = 0x51
DW_OP_reg2 = 0x52
DW_OP_reg3 = 0x53
DW_OP_reg4 = 0x54
DW_OP_reg5 = 0x55
DW_OP_reg6 = 0x56
DW_OP_reg7 = 0x57
DW_OP_reg8 = 0x58
DW_OP_reg9 = 0x59
DW_OP_reg10 = 0x5a
DW_OP_reg11 = 0x5b
DW_OP_reg12 = 0x5c
DW_OP_reg13 = 0x5d
DW_OP_reg14 = 0x5e
DW_OP_reg15 = 0x5f
DW_OP_reg16 = 0x60
DW_OP_reg17 = 0x61
DW_OP_reg18 = 0x62
DW_OP_reg19 = 0x63
DW_OP_reg20 = 0x64
DW_OP_reg21 = 0x65
DW_OP_reg22 = 0x66
DW_OP_reg23 = 0x67
DW_OP_reg24 = 0x68
DW_OP_reg25 = 0x69
DW_OP_reg26 = 0x6a
DW_OP_reg27 = 0x6b
DW_OP_reg28 = 0x6c
DW_OP_reg29 = 0x6d
DW_OP_reg30 = 0x6e
DW_OP_reg31 = 0x6f
DW_OP_breg0 = 0x70
DW_OP_breg1 = 0x71
DW_OP_breg2 = 0x72
DW_OP_breg3 = 0x73
DW_OP_breg4 = 0x74
DW_OP_breg5 = 0x75
DW_OP_breg6 = 0x76
DW_OP_breg7 = 0x77
DW_OP_breg8 = 0x78
DW_OP_breg9 = 0x79
DW_OP_breg10 = 0x7a
DW_OP_breg11 = 0x7b
DW_OP_breg12 = 0x7c
DW_OP_breg13 = 0x7d
DW_OP_breg14 = 0x7e
DW_OP_breg15 = 0x7f
DW_OP_breg16 = 0x80
DW_OP_breg17 = 0x81
DW_OP_breg18 = 0x82
DW_OP_breg19 = 0x83
DW_OP_breg20 = 0x84
DW_OP_breg21 = 0x85
DW_OP_breg22 = 0x86
DW_OP_breg23 = 0x87
DW_OP_breg24 = 0x88
DW_OP_breg25 = 0x89
DW_OP_breg26 = 0x8a
DW_OP_breg27 = 0x8b
DW_OP_breg28 = 0x8c
DW_OP_breg29 = 0x8d
DW_OP_breg30 = 0x8e
DW_OP_breg31 = 0x8f
DW_OP_regx = 0x90
DW_OP_fbreg = 0x91
DW_OP_bregx = 0x92
DW_OP_piece = 0x93
DW_OP_deref_size = 0x94
DW_OP_xderef_size = 0x95
DW_OP_nop = 0x96
DW_OP_push_object_address = 0x97
DW_OP_call2 = 0x98
DW_OP_call4 = 0x99
DW_OP_call_ref = 0x9a
DW_OP_form_tls_address = 0x9b
DW_OP_call_frame_cfa = 0x9c
DW_OP_bit_piece = 0x9d
DW_OP_implicit_value = 0x9e
DW_OP_stack_value = 0x9f
DW_OP_implicit_pointer = 0xa0
DW_OP_addrx = 0xa1
DW_OP_constx = 0xa2
DW_OP_entry_value = 0xa3
DW_OP_const_type = 0xa4
DW_OP_regval_type = 0xa5
DW_OP_deref_type = 0xa6
DW_OP_xderef_type = 0xa7
DW_OP_convert = 0xa8
DW_OP_reinterpret = 0xa9
DW_OP_lo_user = 0xe0
DW_OP_hi_user = 0xff
DW_OP_GNU_push_tls_address = 0xe0
DW_OP_GNU_uninit = 0xf0
DW_OP_GNU_encoded_addr = 0xf1
DW_OP_GNU_implicit_pointer = 0xf2
DW_OP_GNU_entry_value = 0xf3
DW_OP_GNU_const_type = 0xf4
DW_OP_GNU_regval_type = 0xf5
DW_OP_GNU_deref_type = 0xf6
DW_OP_GNU_convert = 0xf7
DW_OP_GNU_reinterpret = 0xf9
DW_OP_GNU_parameter_ref = 0xfa
DW_OP_GNU_addr_index = 0xfb
DW_OP_GNU_const_index = 0xfc
DW_OP_GNU_variable_value = 0xfd
DW_OP_HP_unknown = 0xe0
DW_OP_HP_is_value = 0xe1
DW_OP_HP_fltconst4 = 0xe2
DW_OP_HP_fltconst8 = 0xe3
DW_OP_HP_mod_range = 0xe4
DW_OP_HP_unmod_range = 0xe5
DW_OP_HP_tls = 0xe6
DW_OP_PGI_omp_thread_num = 0xf8
DW_OP_AARCH64_operation = 0xea

DW_OP_NAME_MAP: Dict[int, str] = {
    0x03: 'DW_OP_addr',
    0x06: 'DW_OP_deref',
    0x08: 'DW_OP_const1u',
    0x09: 'DW_OP_const1s',
    0x0a: 'DW_OP_const2u',
    0x0b: 'DW_OP_const2s',
    0x0c: 'DW_OP_const4u',
    0x0d: 'DW_OP_const4s',
    0x0e: 'DW_OP_const8u',
    0x0f: 'DW_OP_const8s',
    0x10: 'DW_OP_constu',
    0x11: 'DW_OP_consts',
    0x12: 'DW_OP_dup',
    0x13: 'DW_OP_drop',
    0x14: 'DW_OP_over',
    0x15: 'DW_OP_pick',
    0x16: 'DW_OP_swap',
    0x17: 'DW_OP_rot',
    0x18: 'DW_OP_xderef',
    0x19: 'DW_OP_abs',
    0x1a: 'DW_OP_and',
    0x1b: 'DW_OP_div',
    0x1c: 'DW_OP_minus',
    0x1d: 'DW_OP_mod',
    0x1e: 'DW_OP_mul',
    0x1f: 'DW_OP_neg',
    0x20: 'DW_OP_not',
    0x21: 'DW_OP_or',
    0x22: 'DW_OP_plus',
    0x23: 'DW_OP_plus_uconst',
    0x24: 'DW_OP_shl',
    0x25: 'DW_OP_shr',
    0x26: 'DW_OP_shra',
    0x27: 'DW_OP_xor',
    0x28: 'DW_OP_bra',
    0x29: 'DW_OP_eq',
    0x2a: 'DW_OP_ge',
    0x2b: 'DW_OP_gt',
    0x2c: 'DW_OP_le',
    0x2d: 'DW_OP_lt',
    0x2e: 'DW_OP_ne',
    0x2f: 'DW_OP_skip',
    0x30: 'DW_OP_lit0',
    0x31: 'DW_OP_lit1',
    0x32: 'DW_OP_lit2',
    0x33: 'DW_OP_lit3',
    0x34: 'DW_OP_lit4',
    0x35: 'DW_OP_lit5',
    0x36: 'DW_OP_lit6',
    0x37: 'DW_OP_lit7',
    0x38: 'DW_OP_lit8',
    0x39: 'DW_OP_lit9',
    0x3a: 'DW_OP_lit10',
    0x3b: 'DW_OP_lit11',
    0x3c: 'DW_OP_lit12',
    0x3d: 'DW_OP_lit13',
    0x3e: 'DW_OP_lit14',
    0x3f: 'DW_OP_lit15',
    0x40: 'DW_OP_lit16',
    0x41: 'DW_OP_lit17',
    0x42: 'DW_OP_lit18',
    0x43: 'DW_OP_lit19',
    0x44: 'DW_OP_lit20',
    0x45: 'DW_OP_lit21',
    0x46: 'DW_OP_lit22',
    0x47: 'DW_OP_lit23',
    0x48: 'DW_OP_lit24',
    0x49: 'DW_OP_lit25',
    0x4a: 'DW_OP_lit26',
    0x4b: 'DW_OP_lit27',
    0x4c: 'DW_OP_lit28',
    0x4d: 'DW_OP_lit29',
    0x4e: 'DW_OP_lit30',
    0x4f: 'DW_OP_lit31',
    0x50: 'DW_OP_reg0',
    0x51: 'DW_OP_reg1',
    0x52: 'DW_OP_reg2',
    0x53: 'DW_OP_reg3',
    0x54: 'DW_OP_reg4',
    0x55: 'DW_OP_reg5',
    0x56: 'DW_OP_reg6',
    0x57: 'DW_OP_reg7',
    0x58: 'DW_OP_reg8',
    0x59: 'DW_OP_reg9',
    0x5a: 'DW_OP_reg10',
    0x5b: 'DW_OP_reg11',
    0x5c: 'DW_OP_reg12',
    0x5d: 'DW_OP_reg13',
    0x5e: 'DW_OP_reg14',
    0x5f: 'DW_OP_reg15',
    0x60: 'DW_OP_reg16',
    0x61: 'DW_OP_reg17',
    0x62: 'DW_OP_reg18',
    0x63: 'DW_OP_reg19',
    0x64: 'DW_OP_reg20',
    0x65: 'DW_OP_reg21',
    0x66: 'DW_OP_reg22',
    0x67: 'DW_OP_reg23',
    0x68: 'DW_OP_reg24',
    0x69: 'DW_OP_reg25',
    0x6a: 'DW_OP_reg26',
    0x6b: 'DW_OP_reg27',
    0x6c: 'DW_OP_reg28',
    0x6d: 'DW_OP_reg29',
    0x6e: 'DW_OP_reg30',
    0x6f: 'DW_OP_reg31',
    0x70: 'DW_OP_breg0',
    0x71: 'DW_OP_breg1',
    0x72: 'DW_OP_breg2',
    0x73: 'DW_OP_breg3',
    0x74: 'DW_OP_breg4',
    0x75: 'DW_OP_breg5',
    0x76: 'DW_OP_breg6',
    0x77: 'DW_OP_breg7',
    0x78: 'DW_OP_breg8',
    0x79: 'DW_OP_breg9',
    0x7a: 'DW_OP_breg10',
    0x7b: 'DW_OP_breg11',
    0x7c: 'DW_OP_breg12',
    0x7d: 'DW_OP_breg13',
    0x7e: 'DW_OP_breg14',
    0x7f: 'DW_OP_breg15',
    0x80: 'DW_OP_breg16',
    0x81: 'DW_OP_breg17',
    0x82: 'DW_OP_breg18',
    0x83: 'DW_OP_breg19',
    0x84: 'DW_OP_breg20',
    0x85: 'DW_OP_breg21',
    0x86: 'DW_OP_breg22',
    0x87: 'DW_OP_breg23',
    0x88: 'DW_OP_breg24',
    0x89: 'DW_OP_breg25',
    0x8a: 'DW_OP_breg26',
    0x8b: 'DW_OP_breg27',
    0x8c: 'DW_OP_breg28',
    0x8d: 'DW_OP_breg29',
    0x8e: 'DW_OP_breg30',
    0x8f: 'DW_OP_breg31',
    0x90: 'DW_OP_regx',
    0x91: 'DW_OP_fbreg',
    0x92: 'DW_OP_bregx',
    0x93: 'DW_OP_piece',
    0x94: 'DW_OP_deref_size',
    0x95: 'DW_OP_xderef_size',
    0x96: 'DW_OP_nop',
    0x97: 'DW_OP_push_object_address',
    0x98: 'DW_OP_call2',
    0x99: 'DW_OP_call4',
    0x9a: 'DW_OP_call_ref',
    0x9b: 'DW_OP_form_tls_address',
    0x9c: 'DW_OP_call_frame_cfa',
    0x9d: 'DW_OP_bit_piece',
    0x9e: 'DW_OP_implicit_value',
    0x9f: 'DW_OP_stack_value',
    0xa0: 'DW_OP_implicit_pointer',
    0xa1: 'DW_OP_addrx',
    0xa2: 'DW_OP_constx',
    0xa3: 'DW_OP_entry_value',
    0xa4: 'DW_OP_const_type',
    0xa5: 'DW_OP_regval_type',
    0xa6: 'DW_OP_deref_type',
    0xa7: 'DW_OP_xderef_type',
    0xa8: 'DW_OP_convert',
    0xa9: 'DW_OP_reinterpret',
    0xe0: 'DW_OP_lo_user/DW_OP_GNU_push_tls_address/DW_OP_HP_unknown',
    0xff: 'DW_OP_hi_user',
    0xf0: 'DW_OP_GNU_uninit',
    0xf1: 'DW_OP_GNU_encoded_addr',
    0xf2: 'DW_OP_GNU_implicit_pointer',
    0xf3: 'DW_OP_GNU_entry_value',
    0xf4: 'DW_OP_GNU_const_type',
    0xf5: 'DW_OP_GNU_regval_type',
    0xf6: 'DW_OP_GNU_deref_type',
    0xf7: 'DW_OP_GNU_convert',
    0xf9: 'DW_OP_GNU_reinterpret',
    0xfa: 'DW_OP_GNU_parameter_ref',
    0xfb: 'DW_OP_GNU_addr_index',
    0xfc: 'DW_OP_GNU_const_index',
    0xfd: 'DW_OP_GNU_variable_value',
    0xe1: 'DW_OP_HP_is_value',
    0xe2: 'DW_OP_HP_fltconst4',
    0xe3: 'DW_OP_HP_fltconst8',
    0xe4: 'DW_OP_HP_mod_range',
    0xe5: 'DW_OP_HP_unmod_range',
    0xe6: 'DW_OP_HP_tls',
    0xf8: 'DW_OP_PGI_omp_thread_num',
    0xea: 'DW_OP_AARCH64_operation',
}

DW_CHILDREN_no = 0x00
DW_CHILDREN_yes = 0x01

DW_DIE_DEPTH_MAX = 999999

# https://sourceware.org/git/?p=glibc.git;a=blob;f=elf/elf.h

# e_ident array fields
EI_MAG0 = 0
EI_MAG1 = 1
EI_MAG2 = 2
EI_MAG3 = 3
ELFMAG = b'\x7fELF'
SELFMAG = 4
EI_CLASS = 4
ELFCLASS32 = 1
ELFCLASS64 = 2
EI_DATA = 5
ELFDATA2LSB = 1
ELFDATA2MSB = 2
EI_VERSION = 6
EI_OSABI = 7
EI_ABIVERSION = 8
EI_NIDENT = 16

# sh_type values
SHT_NULL = 0
SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_RELA = 4
SHT_HASH = 5
SHT_DYNAMIC = 6
SHT_NOTE = 7
SHT_NOBITS = 8
SHT_REL = 9
SHT_SHLIB = 10
SHT_DYNSYM = 11
SHT_INIT_ARRAY = 14
SHT_FINI_ARRAY = 15
SHT_PREINIT_ARRAY = 16
SHT_GROUP = 17
SHT_SYMTAB_SHNDX = 18
SHT_RELR = 19
SHT_NUM = 20
SHT_LOOS = 0x60000000
SHT_GNU_ATTRIBUTES = 0x6ffffff5
SHT_GNU_HASH = 0x6ffffff6
SHT_GNU_LIBLIST = 0x6ffffff7
SHT_CHECKSUM = 0x6ffffff8
SHT_LOSUNW = 0x6ffffffa
SHT_SUNW_move = 0x6ffffffa
SHT_SUNW_COMDAT = 0x6ffffffb
SHT_SUNW_syminfo = 0x6ffffffc
SHT_GNU_verdef = 0x6ffffffd
SHT_GNU_verneed = 0x6ffffffe
SHT_GNU_versym = 0x6fffffff
SHT_HISUNW = 0x6fffffff
SHT_HIOS = 0x6fffffff
SHT_LOPROC = 0x70000000
SHT_HIPROC = 0x7fffffff
SHT_LOUSER = 0x80000000
SHT_HIUSER = 0x8fffffff


SHT_NAME_MAP: Dict[int, str] = {
    SHT_NULL: 'NULL',
    SHT_PROGBITS: 'PROGBITS',
    SHT_SYMTAB: 'SYMTAB',
    SHT_STRTAB: 'STRTAB',
    SHT_RELA: 'RELA',
    SHT_HASH: 'HASH',
    SHT_DYNAMIC: 'DYNAMIC',
    SHT_NOTE: 'NOTE',
    SHT_NOBITS: 'NOBITS',
    SHT_REL: 'REL',
    SHT_SHLIB: 'SHLIB',
    SHT_DYNSYM: 'DYNSYM',
    SHT_INIT_ARRAY: 'INIT_ARRAY',
    SHT_FINI_ARRAY: 'FINI_ARRAY',
    SHT_PREINIT_ARRAY: 'PREINIT_ARRAY',
    SHT_GROUP: 'GROUP',
    SHT_SYMTAB_SHNDX: 'SYMTAB_SHNDX',
    SHT_RELR: 'RELR',
    SHT_NUM: 'NUM',
    SHT_LOOS: 'LOOS',
    SHT_GNU_ATTRIBUTES: 'GNU_ATTRIBUTES',
    SHT_GNU_HASH: 'GNU_HASH',
    SHT_GNU_LIBLIST: 'GNU_LIBLIST',
    SHT_CHECKSUM: 'CHECKSUM',
    SHT_LOSUNW: 'LOSUNW',
    SHT_SUNW_move: 'SUNW_move',
    SHT_SUNW_COMDAT: 'SUNW_COMDAT',
    SHT_SUNW_syminfo: 'SUNW_syminfo',
    SHT_GNU_verdef: 'GNU_verdef',
    SHT_GNU_verneed: 'GNU_verneed',
    SHT_GNU_versym: 'GNU_versym',
    SHT_HISUNW: 'HISUNW',
    SHT_HIOS: 'HIOS',
    SHT_LOPROC: 'LOPROC',
    SHT_HIPROC: 'HIPROC',
    SHT_LOUSER: 'LOUSER',
    SHT_HIUSER: 'HIUSER',
}


def get_sht_name(sht: int) -> str:
    return SHT_NAME_MAP[sht] if sht in SHT_NAME_MAP else f'UNKNOWN {sht}'


# ST_BIND subfield values
STB_LOCAL = 0
STB_GLOBAL = 1
STB_WEAK = 2
STB_NUM = 3
STB_LOOS = 10
STB_GNU_UNIQUE = 10
STB_HIOS = 12
STB_LOPROC = 13
STB_HIPROC = 15

STB_NAME_MAP: Dict[int, str] = {
    0: 'LOCAL',
    1: 'GLOBAL',
    2: 'WEAK',
    3: 'NUM',
    10: 'LOOS',
    12: 'HIOS',
    13: 'LOPROC',
    15: 'HIPROC',
}

# ST_TYPE subfield values
STT_NOTYPE = 0
STT_OBJECT = 1
STT_FUNC = 2
STT_SECTION = 3
STT_FILE = 4
STT_COMMON = 5
STT_TLS = 6
STT_NUM = 7
STT_LOOS = 10
STT_GNU_IFUNC = 10
STT_HIOS = 12
STT_LOPROC = 13
STT_HIPROC = 15

STT_NAME_MAP: Dict[int, str] = {
    0: 'NOTYPE',
    1: 'OBJECT',
    2: 'FUNC',
    3: 'SECTION',
    4: 'FILE',
    5: 'COMMON',
    6: 'TLS',
    7: 'NUM',
    10: 'LOOS/GNU_IFUNC',
    12: 'HIOS',
    13: 'LOPROC',
    15: 'HIPROC',
}

# Symbol visibility
STV_DEFAULT = 0
STV_INTERNAL = 1
STV_HIDDEN = 2
STV_PROTECTED = 3

STV_NAME_MAP: Dict[int, str] = {
    0: 'DEFAULT',
    1: 'INTERNAL',
    2: 'HIDDEN',
    3: 'PROTECTED',
}

# Special section indices
SHN_UNDEF = 0
SHN_LORESERVE = 0xff00
SHN_LOPROC = 0xff00
SHN_BEFORE = 0xff00
SHN_AFTER = 0xff01
SHN_HIPROC = 0xff1f
SHN_LOOS = 0xff20
SHN_HIOS = 0xff3f
SHN_ABS = 0xfff1
SHN_COMMON = 0xfff2
SHN_XINDEX = 0xffff
SHN_HIRESERVE = 0xffff

# Section header sh_flags values
SHF_WRITE = (1 << 0)
SHF_ALLOC = (1 << 1)
SHF_EXECINSTR = (1 << 2)
SHF_MERGE = (1 << 4)
SHF_STRINGS = (1 << 5)
SHF_INFO_LINK = (1 << 6)
SHF_LINK_ORDER = (1 << 7)
SHF_OS_NONCONFORMING = (1 << 8)
SHF_GROUP = (1 << 9)
SHF_TLS = (1 << 10)
SHF_COMPRESSED = (1 << 11)
SHF_MASKOS = 0x0ff00000
SHF_MASKPROC = 0xf0000000
SHF_GNU_RETAIN  = (1 << 21)
SHF_ORDERED = (1 << 30)
SHF_EXCLUDE = (1 << 31)


class Elf_Exception(Exception):
    pass


@dataclass
class Elf_Ehdr:
    FMT32: ClassVar[str] = '16s2H5L6H'
    FMT64: ClassVar[str] = '16s2HL3QL6H'

    e_ident: bytes
    e_type: int
    e_machine: int
    e_version: int
    e_entry: int
    e_phoff: int
    e_shoff: int
    e_flags: int
    e_ehsize: int
    e_phentsize: int
    e_phnum: int
    e_shentsize: int
    e_shnum: int
    e_shstrndx: int


@dataclass
class Elf_Phdr:
    FMT32: ClassVar[str] = '8L'
    FMT64: ClassVar[str] = '2L6Q'

    _elf: 'Elf'

    p_type: int
    p_offset: int
    p_vaddr: int
    p_paddr: int
    p_filesz: int
    p_memsz: int
    p_flags: int
    p_align: int


@dataclass
class Elf_Shdr:
    FMT32: ClassVar[str] = '10L'
    FMT64: ClassVar[str] = '2L4Q2L2Q'

    _elf: 'Elf'

    sh_name: int
    sh_type: int
    sh_flags: int
    sh_addr: int
    sh_offset: int
    sh_size: int
    sh_link: int
    sh_info: int
    sh_addralign: int
    sh_entsize: int

    _data: Optional[bytes] = None
    _name: Optional[str] = None

    @property
    def data(self) -> bytes:
        if self._data is None:
            self._data = self._elf.read(self.sh_offset, self.sh_size)
        return self._data

    @property
    def name(self) -> str:
        if self._name is None:
            self._name = self._elf.lookup_string(self._elf.shdrs[self._elf.ehdr.e_shstrndx], self.sh_name).decode()
        return self._name


@dataclass
class Elf_Sym:
    FMT32: ClassVar[str] = '3L2BH'
    FMT64: ClassVar[str] = 'L2BH2Q'

    _elf: 'Elf'
    _strndx: int

    st_name: int
    st_value: int
    st_size: int
    st_info: int
    st_other: int
    st_shndx: int

    cu_name: Optional[str] = None
    _name: Optional[str] = None

    def __init__(self, elf: 'Elf', sh_link: int, values: Tuple[int, ...]) -> None:
        self._elf = elf
        self._strndx = sh_link
        ei_class = elf.ehdr.e_ident[EI_CLASS]
        # The 32-bit and 64-bit versions have the same members, just in a different order.
        if ei_class == ELFCLASS32:
            self.st_name = values[0]
            self.st_value = values[1]
            self.st_size = values[2]
            self.st_info = values[3]
            self.st_other = values[4]
            self.st_shndx = values[5]
        else:
            self.st_name = values[0]
            self.st_info = values[1]
            self.st_other = values[2]
            self.st_shndx = values[3]
            self.st_value = values[4]
            self.st_size = values[5]

    @property
    def name(self) -> str:
        if self._name is None:
            self._name = self._elf.lookup_string(self._elf.shdrs[self._strndx], self.st_name).decode()
        return self._name

    @property
    def type(self) -> int:
        return self.st_info & 0xf

    @property
    def type_name(self) -> str:
        return STT_NAME_MAP[self.type]

    @property
    def bind(self) -> int:
        return self.st_info >> 4

    @property
    def bind_name(self) -> str:
        return STB_NAME_MAP[self.bind]

    @property
    def visibility(self) -> int:
        return self.st_other & 0x03

    @property
    def visibility_name(self) -> str:
        return STV_NAME_MAP[self.visibility]


@dataclass
class Dwarf_Abbrev_Attr:
    attr: int
    form: int
    size: int
    value: Optional[Any]
    offset: int

    _elf: 'Elf'

    def __init__(self, elf: 'Elf', data: bytes, offset: int) -> None:
        self.offset = offset
        self._elf = elf

        self.attr, offset = elf.get_uleb128(data, offset)
        self.form, offset = elf.get_uleb128(data, offset)
        if self.form == DW_FORM_implicit_const:
            # Dwarf5: 7.5.3 Abbreviations Tables
            # The attribute form DW_FORM_implicit_const is another special case. For
            # attributes with this form, the attribute specification contains a third part, which is
            # a signed LEB128 number. The value of this number is used as the value of the
            # attribute, and no value is stored in the .debug_info section.
            self.value, offset = elf.get_uleb128(data, offset)
        else:
            self.value = None
        self.size = offset - self.offset

    @property
    def attr_name(self) -> str:
        return DW_AT_NAME_MAP[self.attr] if self.attr in DW_AT_NAME_MAP else f'UNKNOWN {self.attr}'

    @property
    def form_name(self) -> str:
        return DW_FORM_NAME_MAP[self.form] if self.form in DW_FORM_NAME_MAP else f'UNKNOWN {self.form}'


@dataclass
class Dwarf_Abbrev_Entry:
    code: int
    tag: int
    children: int
    offset: int
    size: int
    attrs: List[Dwarf_Abbrev_Attr]

    _elf: 'Elf'

    def __init__(self, elf: 'Elf', data: bytes, offset: int) -> None:
        self.offset = offset
        self._elf = elf
        self.attrs = []

        self.code, offset = elf.get_uleb128(data, offset)
        self.tag, offset = elf.get_uleb128(data, offset)
        self.children, offset = elf.get_uint8(data, offset)
        while True:
            attr = Dwarf_Abbrev_Attr(elf, data, offset)
            self.attrs.append(attr)
            offset += attr.size
            if attr.attr == DW_AT_end and attr.form == DW_FORM_end:
                # The series of attribute specifications ends with an entry
                # containing 0 for the name and 0 for the form.
                break

        self.size = offset - self.offset

    @property
    def tag_name(self) -> str:
        return DW_TAG_NAME_MAP[self.tag] if self.tag in DW_TAG_NAME_MAP else f'UNKNOWN {self.tag}'


@dataclass
class Dwarf_CU:
    offset: int  # offset into the .debug_info section data for CU
    unit_length: bytes
    length: int
    version: int
    unit_type: int
    address_size: int
    debug_abbrev_offset: int
    size: int

    _elf: 'Elf'
    _abbrev_table: Optional[List[Optional[Dwarf_Abbrev_Entry]]]
    _die: Optional[Dict[int, Any]]
    _die_offset: int  # offset into the .debug_info for the first DIE
    _data: bytes  # .debug_info section data
    get_address: Callable  # Dwarf5: 32-bit or 64-bit offset, Dwarf5: 7.5.1.1 Full and Partial Compilation Unit Headers
    get_offset: Callable  # Dwarf5: 7.4 32-Bit and 64-Bit DWARF Formats

    def __init__(self, elf: 'Elf', data: bytes, offset: int):
        self._elf = elf
        self._abbrev_table = None
        self._die = None
        self._data = data

        self.offset = offset

        self.unit_length, _ = elf.get_bytes(4, data, offset)
        self.length, offset = elf.get_uint32(data, offset)
        self.size = 4 + self.length

        self.get_offset = elf.get_uint32

        if self.length == 0xffffffff:
            self.get_offset = elf.get_uint64
            unit_length, _ = elf.get_bytes(8, data, offset)
            self.unit_length += unit_length

            self.length, offset = elf.get_uint64(data, offset)
            self.size = 12 + self.length

        self.version, offset = elf.get_uint16(data, offset)

        if self.version == 5:
            self.unit_type, offset = elf.get_uint8(data, offset)
            self.address_size, offset = elf.get_uint8(data, offset)
            self.debug_abbrev_offset, offset = self.get_offset(data, offset)
        elif self.version <= 4:
            self.debug_abbrev_offset, offset = self.get_offset(data, offset)
            self.address_size, offset = elf.get_uint8(data, offset)
        else:
            raise Elf_Exception(f'unsupported DWARF version {self.version}')

        if self.address_size == 4:
            self.get_address = elf.get_uint32
        elif self.address_size == 8:
            self.get_address = elf.get_uint64
        else:
            raise Elf_Exception(f'unknown DWARF address size {self.address_size}')

        self._die_offset = offset

    @property
    def abbrev_table(self) -> List:
        if self._abbrev_table is not None:
            return self._abbrev_table

        self._abbrev_table = [None]

        shdr = self._elf.lookup_shdr('.debug_abbrev')
        if shdr is None:
            return self._abbrev_table

        data = shdr.data
        offset = self.debug_abbrev_offset

        while True:
            code, _ = self._elf.get_uleb128(data, offset)
            if not code:
                # The abbreviations for a given compilation unit end with an entry consisting of a
                # 0 byte for the abbreviation code.
                break

            entry = Dwarf_Abbrev_Entry(self._elf, data, offset)
            self._abbrev_table.append(entry)
            offset += entry.size

        return self._abbrev_table

    def get_attr_value(self, abbrev_attr: Dwarf_Abbrev_Attr, data: bytes, offset: int) -> Tuple[Any, int]:
        # Dwarf5: 7.5.5 Classes and Forms
        value = None
        form = abbrev_attr.form

        # address class
        if form == DW_FORM_addr:
            value, offset = self.get_address(data, offset)

        # addrptr class
        elif form == DW_FORM_sec_offset:
            value, offset = self.get_offset(data, offset)

        # block class
        elif form == DW_FORM_block1:
            size, offset = self._elf.get_uint8(data, offset)
            value, offset = self._elf.get_bytes(size, data, offset)
        elif form == DW_FORM_block2:
            size, offset = self._elf.get_uint16(data, offset)
            value, offset = self._elf.get_bytes(size, data, offset)
        elif form == DW_FORM_block4:
            size, offset = self._elf.get_uint32(data, offset)
            value, offset = self._elf.get_bytes(size, data, offset)
        elif form == DW_FORM_block:
            size, offset = self._elf.get_uleb128(data, offset)
            value, offset = self._elf.get_bytes(size, data, offset)

        # constant class
        elif form == DW_FORM_data1:
            value, offset = self._elf.get_uint8(data, offset)
        elif form == DW_FORM_data2:
            value, offset = self._elf.get_uint16(data, offset)
        elif form == DW_FORM_data4:
            value, offset = self._elf.get_uint32(data, offset)
        elif form == DW_FORM_data8:
            value, offset = self._elf.get_uint64(data, offset)
        elif form == DW_FORM_data16:
            value, offset = self._elf.get_uint128(data, offset)
        elif form == DW_FORM_udata:
            value, offset = self._elf.get_uleb128(data, offset)
        elif form == DW_FORM_sdata:
            value, offset = self._elf.get_sleb128(data, offset)
        elif form == DW_FORM_implicit_const:
            # Value is provided as part of the abbreviation declaration
            value = abbrev_attr.value

        # exprloc class
        elif form == DW_FORM_exprloc:
            size, offset = self._elf.get_uleb128(data, offset)
            value, offset = self._elf.get_bytes(size, data, offset)

        # flag class
        elif form == DW_FORM_flag:
            value, offset = self._elf.get_uint8(data, offset)
        elif form == DW_FORM_flag_present:
            value = True

        # lineptr class
        # DW_FORM_sec_offset handled in addrptr class

        # loclist class
        elif form == DW_FORM_loclistx:
            size, offset = self._elf.get_uleb128(data, offset)
        # DW_FORM_sec_offset handled in addrptr class

        # loclistsptr class
        # DW_FORM_sec_offset handled in addrptr class

        # macptr class
        # DW_FORM_sec_offset handled in addrptr class

        # rnglist class
        elif form == DW_FORM_rnglistx:
            size, offset = self._elf.get_uleb128(data, offset)
        # DW_FORM_sec_offset handled in addrptr class

        # rnglistsptr
        # DW_FORM_sec_offset handled in addrptr class

        # reference class
        elif form == DW_FORM_ref1:
            value, offset = self._elf.get_uint8(data, offset)
            value += self.offset
        elif form == DW_FORM_ref2:
            value, offset = self._elf.get_uint16(data, offset)
            value += self.offset
        elif form == DW_FORM_ref4:
            value, offset = self._elf.get_uint32(data, offset)
            value += self.offset
        elif form == DW_FORM_ref8:
            value, offset = self._elf.get_uint64(data, offset)
            value += self.offset
        elif form == DW_FORM_ref_udata:
            value, offset = self._elf.get_uleb128(data, offset)
            value += self.offset
        elif form == DW_FORM_ref_addr:
            value, offset = self.get_offset(data, offset)
        elif form == DW_FORM_ref_sig8:
            value, offset = self._elf.get_uint8(data, offset)
        elif form == DW_FORM_ref_sup4:
            value, offset = self._elf.get_uint32(data, offset)
        elif form == DW_FORM_ref_sup8:
            value, offset = self._elf.get_uint64(data, offset)

        # string class
        elif form == DW_FORM_string:
            value, offset = self._elf.get_string(data, offset)
        elif form == DW_FORM_strp:
            value, offset = self.get_offset(data, offset)
        elif form == DW_FORM_line_strp:
            value, offset = self.get_offset(data, offset)
        elif form == DW_FORM_strp_sup:
            value, offset = self.get_offset(data, offset)
        elif form == DW_FORM_strx:
            value, offset = self._elf.get_uleb128(data, offset)
        elif form == DW_FORM_strx1:
            value, offset = self._elf.get_uint8(data, offset)
        elif form == DW_FORM_strx2:
            value, offset = self._elf.get_uint16(data, offset)
        elif form == DW_FORM_strx3:
            value, offset = self._elf.get_uint24(data, offset)
        elif form == DW_FORM_strx4:
            value, offset = self._elf.get_uint32(data, offset)

        # unknown class/form
        else:
            name = DW_FORM_NAME_MAP.get(form, 'unknown')
            raise Elf_Exception(f'unknown dwarf form {form:#x} {name}')

        return value, offset

    def get_attr_eval(self, attr: Dict[str, Any]) -> Optional[Any]:
        if 'evaluated' in attr:
            return attr['eval']

        form = attr['form']
        value = attr['value']
        evaluated = None

        if form == DW_FORM_strp:
            shdr = self._elf.lookup_shdr('.debug_str')
            evaluated = self._elf.lookup_string(shdr, int(value)).decode() if shdr else None
        elif form == DW_FORM_line_strp:
            shdr = self._elf.lookup_shdr('.debug_line_str')
            evaluated = self._elf.lookup_string(shdr, int(value)).decode() if shdr else None

        elif form == DW_FORM_string:
            assert type(value) == bytes
            evaluated = value.decode()

        elif form == DW_FORM_exprloc:
            # Dwarf5: 2.5 DWARF Expressions
            # This handles only DW_OP_addr, which is probably the only one we need.
            # Fully implement DWARF expressions is not possible, because some
            # expressions work with registers content, which is not available, unless
            # the real debugging is taking place.
            assert type(value) == bytes

            stack: List[Any] = []

            offset = 0
            while offset < len(value):
                b = value[offset]
                offset += 1

                if b == DW_OP_addr:
                    res, offset = self._elf.get_address(value, offset)
                    stack.append(res)
                else:
                    # Not implemented
                    stack = [None]
                    break

            if len(stack) != 1:
                raise Elf_Exception(f'invalid DWARF stack {stack}')

            evaluated = stack.pop()

        else:
            # Evaluation of form is not supported.
            evaluated = None

        attr['evaluated'] = evaluated
        return evaluated

    def get_attr_str(self, attr: Dict[str, Any]) -> str:
        if 'string' in attr:
            return str(attr['string'])

        string = ''
        value = self.get_attr_eval(attr)
        if value is None:
            # Not implemented, return raw value
            value = attr['value']

        if isinstance(value, str):
            string = value
        elif isinstance(value, bytes):
            string = value.hex()
        else:
            string = f'{value:#x}'

        attr['string'] = string
        return string

    @property
    def DIEs(self) -> Dict[int, Any]:
        return self.get_DIEs()

    def get_DIEs(self, filter_tags: Optional[List[int]] = None) -> Dict[int, Any]:
        if self._die:
            return self._die

        dies: Dict[int, Any] = {}
        self._die = dies

        def get_dwarf_attr(abbrev_attr: Dwarf_Abbrev_Attr, data: bytes, offset: int) -> Dict[str, Any]:
            attr: Dict[str, Any] = {
                'attr': abbrev_attr.attr,
                'form': abbrev_attr.form,
                'offset': offset,
                'value': None,
                'size': None,
            }

            value, offset = self.get_attr_value(abbrev_attr, data, offset)
            attr['value'] = value
            attr['size'] = offset - attr['offset']

            return attr

        def get_DIE(offset: int, parent: Optional[int] = None, level: int = 0) -> Dict[str, Any]:
            die: Dict[str, Any] = {
                'offset': offset,
                'parent': parent,
                'level': level,
                'code': None,
                'tag': None,
                'size': None,
                'attrs': {},
            }

            code, offset = self._elf.get_uleb128(self._data, offset)
            die['code'] = code

            if die['code'] == 0:
                # Dwarf5: 7.5.2 Debugging Information Entry
                # On some architectures, there are alignment constraints on section boundaries. To
                # make it easier to pad debugging information sections to satisfy such constraints,
                # the abbreviation code 0 is reserved. Debugging information entries consisting of
                # only the abbreviation code 0 are considered null entries.
                die['size'] = offset - die['offset']
                die['tag'] = DW_TAG_padding
                if filter_tags is None or die['tag'] in filter_tags:
                    dies[die['offset']] = die
                return die

            abbrev_entry = self.abbrev_table[die['code']]
            die['tag'] = abbrev_entry.tag
            if filter_tags is None or die['tag'] in filter_tags:
                dies[die['offset']] = die
            # Sanity check that abbreviation code in .debug_info matches code in .debug_abbrev
            assert die['code'] == abbrev_entry.code

            for abbrev_attr in abbrev_entry.attrs:
                if abbrev_attr.attr == DW_AT_end:
                    break

                attr = get_dwarf_attr(abbrev_attr, self._data, offset)
                die['attrs'][attr['attr']] = attr
                offset += attr['size']

            if abbrev_entry.children == DW_CHILDREN_no:
                die['size'] = offset - die['offset']
                return die

            while True:
                child = get_DIE(offset, die['offset'], level + 1)
                offset += child['size']

                if child['code'] == 0:
                    # A chain of sibling entries is terminated by a null entry.
                    break

            die['size'] = offset - die['offset']
            return die

        get_DIE(self._die_offset)
        return dies


class Elf:
    def __init__(self, fn: str):
        self.fd = open(fn, 'rb')
        self.fn = fn
        self.ehdr: Elf_Ehdr
        self.phdrs: List[Elf_Phdr] = []
        self.shdrs: List[Elf_Shdr] = []
        self._symbols: Optional[List[Elf_Sym]] = None
        self._CUs: Optional[List[Dwarf_CU]] = None
        self._byteorder: str  # Literal['little', 'big'] added in 3.8

        e_ident = self.read(0, EI_NIDENT)

        ei_magic = e_ident[0:SELFMAG]
        if ei_magic != ELFMAG:
            raise Elf_Exception(f'invalid ELF magic {ei_magic!r}')

        ei_data = e_ident[EI_DATA]
        if ei_data == ELFDATA2LSB:
            self._byteorder = 'little'
        elif ei_data == ELFDATA2MSB:
            self._byteorder = 'big'
        else:
            raise Elf_Exception(f'invalid ELF data {ei_data!r}')

        ehdr_fmt = phdr_fmt = shdr_fmt = self._sym_fmt = ''

        ei_class = e_ident[EI_CLASS]
        if ei_class == ELFCLASS32:
            ehdr_fmt += Elf_Ehdr.FMT32
            phdr_fmt += Elf_Phdr.FMT32
            shdr_fmt += Elf_Shdr.FMT32
            self._sym_fmt += Elf_Sym.FMT32
        elif ei_class == ELFCLASS64:
            ehdr_fmt += Elf_Ehdr.FMT64
            phdr_fmt += Elf_Phdr.FMT64
            shdr_fmt += Elf_Shdr.FMT64
            self._sym_fmt += Elf_Sym.FMT64
        else:
            raise Elf_Exception(f'invalid ELF class {ei_class}')

        data = self.read(0, struct.calcsize(ehdr_fmt))
        hdr, _ = self.get_fmt(ehdr_fmt, data)
        self.ehdr = Elf_Ehdr(*hdr)  # type: ignore

        if self.ehdr.e_phnum:
            size = self.ehdr.e_phnum * self.ehdr.e_phentsize
            data = self.read(self.ehdr.e_phoff, size)

            offset = 0
            while offset < size:
                hdr, offset = self.get_fmt(phdr_fmt, data, offset)
                self.phdrs.append(Elf_Phdr(self, *hdr))  # type: ignore

        if self.ehdr.e_shnum:
            size = self.ehdr.e_shnum * self.ehdr.e_shentsize
            data = self.read(self.ehdr.e_shoff, size)

            offset = 0
            while offset < size:
                hdr, offset = self.get_fmt(shdr_fmt, data, offset)
                self.shdrs.append(Elf_Shdr(self, *hdr))  # type: ignore

    def __del__(self) -> None:
        if hasattr(self, 'fd'):
            self.fd.close()

    @property
    def symbols(self) -> List[Elf_Sym]:
        if self._symbols is not None:
            return self._symbols

        self._symbols = []

        for shdr in self.shdrs:
            if shdr.sh_type not in (SHT_SYMTAB, SHT_DYNSYM):
                continue

            offset = 0
            while offset < shdr.sh_size:
                sym, offset = self.get_fmt(self._sym_fmt, shdr.data, offset)
                self._symbols.append(Elf_Sym(self, shdr.sh_link, sym))  # type: ignore

        return self._symbols

    @property
    def CUs(self) -> List[Dwarf_CU]:
        if self._CUs is not None:
            return self._CUs

        self._CUs = []

        shdr = self.lookup_shdr('.debug_info')
        if shdr is None:
            return self._CUs

        offset = 0

        while offset < len(shdr.data):
            cu = Dwarf_CU(self, shdr.data, offset)
            # Dwarf5: 7.5.1.1 CU length does not include size of the unit_length field
            offset += len(cu.unit_length) + cu.length
            self._CUs.append(cu)

        return self._CUs

    def read(self, offset: int, count: int) -> bytes:
        self.fd.seek(offset)
        data = self.fd.read(count)
        if len(data) != count:
            raise Elf_Exception(f'error while reading ELF file at offset {offset}')
        return data

    def lookup_string(self, shdr: Elf_Shdr, index: int) -> bytes:
        end = shdr.data.index(b'\x00', index)
        return shdr.data[index:end]

    def lookup_shdr(self, name: str) -> Optional[Elf_Shdr]:
        for shdr in self.shdrs:
            if shdr.name == name:
                return shdr
        return None

    def get_fmt(self, fmt: str, data: bytes, offset: int=0) -> Tuple[Tuple[Union[int, bytes], ...], int]:
        endian = '<' if self._byteorder == 'little' else '>'
        return (struct.unpack_from(endian + fmt, data, offset), offset + struct.calcsize(endian + fmt))

    def get_bytes(self, cnt: int, data: bytes, offset: int=0) -> Tuple[bytes, int]:
        value = data[offset:offset + cnt]
        offset += cnt
        return value, offset

    def get_string(self, data: bytes, offset: int=0) -> Tuple[bytes, int]:
        end = data.index(b'\x00', offset)
        value = data[offset:end]
        return value, end + 1

    def get_int(self, data: bytes, size: int, offset: int=0, signed: bool=False) -> Tuple[int, int]:
        value = int.from_bytes(data[offset:offset + size], byteorder=self._byteorder, signed=signed)  # type: ignore
        offset += size
        return value, offset

    def get_uint8(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 1, offset)

    def get_uint16(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 2, offset)

    def get_uint24(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 3, offset)

    def get_uint32(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 4, offset)

    def get_uint64(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 8, offset)

    def get_uint128(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 16, offset)

    def get_sint8(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 1, offset, True)

    def get_sint16(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 2, offset, True)

    def get_sint24(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 3, offset, True)

    def get_sint32(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 4, offset, True)

    def get_sint64(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 8, offset, True)

    def get_sint128(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        return self.get_int(data, 16, offset, True)

    def get_address(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        ei_class = self.ehdr.e_ident[EI_CLASS]
        if ei_class == ELFCLASS32:
            return self.get_uint32(data, offset)
        else:
            return self.get_uint64(data, offset)

    def get_uleb128(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        # Unsigned Little Endian Base 128
        # Dwarf5: Figure C.3: Algorithm to decode an unsigned LEB128 integer
        res = idx = 0
        while True:
            res |= (data[offset + idx] & 0x7f) << (idx * 7)
            idx += 1
            if not data[offset + idx - 1] & 0x80:
                break
        return res, offset + idx

    def get_sleb128(self, data: bytes, offset: int=0) -> Tuple[int, int]:
        # Signed Little Endian Base 128
        # Dwarf5: Figure C.4: Algorithm to decode a signed LEB128 integer

        # SLEB128 is stored in two's complement, use ULEB128 and
        # sign extend it if necessary.
        value, offset_new = self.get_uleb128(data, offset)
        msb = data[offset - 1]
        if not msb & 0x40:
            # SLEB128 sign bit is 7'th bit in MSB. If not set
            # it's not negative number.
            return value, offset_new

        # Sign extend the value
        value |= - (1 << ((offset_new - offset) * 7))
        return value, offset_new

    def add_cus_to_symbols(self) -> Dict[int, Elf_Sym]:
        dies: Dict[int, Dict[str, Any]] = {}
        syms_dict: Dict[int, Elf_Sym] = {}

        def get_cu_name(die: Dict[str, Any]) -> str:
            dw_at_abstract_origin = die['attrs'].get(DW_AT_abstract_origin)
            if dw_at_abstract_origin:
                die = dies[int(dw_at_abstract_origin['value'])]

            cu = die['cu']
            cu_die = dies[cu._die_offset]

            cu_name = cu.get_attr_str(cu_die['attrs'][DW_AT_name])
            return str(cu_name)

        for cu in self.CUs:
            cu_dies = cu.get_DIEs([DW_TAG_compile_unit, DW_TAG_subprogram, DW_TAG_variable])
            for die in cu_dies.values():
                die['cu'] = cu
            dies.update(cu_dies)

        # Filter symbol table for functions and objects which address is not absolutely set(SHN_ABS).
        # Symbols with SHN_ABS section are mapped to first stage bootloader via linker scripts.
        syms_dict = {sym.st_value: sym for sym in self.symbols
                     if sym.st_size and sym.type in (STT_FUNC, STT_OBJECT) and sym.st_shndx != SHN_ABS}

        for offset, die in dies.items():
            if die['tag'] == DW_TAG_subprogram:
                dw_at_low_pc = die['attrs'].get(DW_AT_low_pc)
                if not dw_at_low_pc:
                    # Dwarf5: 3.3.3 Subroutine and Entry Point Locations
                    # A subroutine entry representing a subroutine declaration that is not also a
                    # definition does not have code address or range attributes.
                    continue

                addr = int(dw_at_low_pc['value'])
                if addr not in syms_dict:
                    # Address not in symbol table
                    continue

                syms_dict[addr].cu_name = get_cu_name(die)

            elif die['tag'] == DW_TAG_variable:
                dw_at_location = die['attrs'].get(DW_AT_location)
                if not dw_at_location:
                    continue

                evaluated = die['cu'].get_attr_eval(dw_at_location)
                if evaluated is None:
                    continue

                addr = int(evaluated)
                if addr not in syms_dict:
                    # Address not in symbol table
                    continue

                syms_dict[addr].cu_name = get_cu_name(die)

        return syms_dict

    def dump_abbrev_table(self) -> None:
        for idx, cu in enumerate(self.CUs):
            print(f'<{cu.debug_abbrev_offset:#010x}> CU<{idx}> at offset {cu.offset:#010x}')
            for entry in cu.abbrev_table:
                if entry is None:
                    continue
                print(f'<{entry.offset:#010x}>{" ":3}{entry.code} {entry.tag_name} [{entry.children}]')
                for attr in entry.attrs:
                    print(f'<{attr.offset:#010x}>{" ":6}{attr.attr_name:30} {attr.form_name}')

    def dump_debug_info(self) -> None:
        for cu in self.CUs:
            dies = cu.get_DIEs()
            for die in dies.values():
                level = die['level']
                offset = die['offset']
                code = die['code']
                size = die['size']
                tag_name = get_tag_name(die['tag'])
                print(f'<{level}> <{offset:#x}> Abbrev Number: <{code}> ({tag_name}) size: {size:#x}')
                for attr in die['attrs'].values():
                    offset = attr['offset']
                    attr_name = get_attr_name(attr['attr'])
                    form_name = get_form_name(attr['form'])
                    value = cu.get_attr_str(attr)
                    print(f'    <{offset:#x}> {attr_name:30}{form_name:30} {value}')

    def dump_symbol_table(self, symbols: Optional[List[Elf_Sym]]=None) -> None:
        if symbols is None:
            symbols = self.symbols

        print(f'{"Num":<7} {"Value":10} {"Size":>7} {"Type":10} {"Bind":10} {"Vis":10} {"Ndx":>6} {"Shdr":20} Name')
        for idx, sym in enumerate(symbols):
            cu_name = f'{sym.cu_name}' if sym.cu_name is not None else 'NOCU'
            shdr_name = elf.shdrs[sym.st_shndx].name if sym.st_shndx < len(elf.shdrs) else 'SPECIAL'
            print((f'{idx:<7} {sym.st_value:#010x} {sym.st_size:7} {sym.type_name:10} '
                   f'{sym.bind_name:10} {sym.visibility_name:10} {sym.st_shndx:6} {shdr_name:20} {sym.name} '
                   f'{cu_name}'))

    def dump_symbol_cu(self) -> None:
        syms_dict = self.add_cus_to_symbols()
        self.dump_symbol_table(list(syms_dict.values()))

    def dump_sections(self) -> None:
        print(f'{"Nr":<3} {"Name":30} {"Type":15} {"Address":10} {"Off":8} {"Size":8}')
        for idx, shdr in enumerate(self.shdrs):
            sht_name = get_sht_name(shdr.sh_type)
            print(f'{idx:<3} {shdr.name:30} {sht_name:15} {shdr.sh_addr:#010x} {shdr.sh_offset:#08x} {shdr.sh_size:#08x}')


if __name__ == '__main__':
    # For testing purposes of this module.
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog='elf',
        description='Testing utility for the ELF/DWARF parser')

    parser.add_argument('-S', '--sections',
                        action='store_true',
                        help='Displays  the  information contained in the section headers')
    parser.add_argument('-s', '--symbols',
                        action='store_true',
                        help='Displays the entries in symbol table section')
    parser.add_argument('-d', '--debug',
                        choices=['info', 'abbrev', 'files'],
                        help=('Displays the contents of the DWARF debug sections in the file. '
                              'info: .debug_info, abbrev: .debug_info, files: .symtab with CUs'))
    parser.add_argument('elf_file',
                        metavar='FILE',
                        help='ELF file')

    args = parser.parse_args()

    elf = Elf(args.elf_file)

    if args.debug == 'info':
        elf.dump_debug_info()
    elif args.debug == 'abbrev':
        elf.dump_abbrev_table()
    elif args.debug == 'files':
        elf.dump_symbol_cu()
    elif args.symbols:
        elf.dump_symbol_table()
    elif args.sections:
        elf.dump_sections()
    else:
        parser.print_help(sys.stderr)
