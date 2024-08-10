Profiling results for FileGraph.from_repo:
         20852429 function calls (19366819 primitive calls) in 16.548 seconds

   Ordered by: cumulative time
   List reduced from 500 to 40 due to restriction <40>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000   16.872   16.872 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\file_resolution\file_graph.py:36(from_repo)
        1    0.000    0.000   13.787   13.787 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\file_resolution\file_graph.py:28(__init__)
        1    0.003    0.003   13.750   13.750 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\repo_resolution\repo_graph.py:36(__init__)
        1    0.017    0.017   11.235   11.235 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\repo_resolution\repo_graph.py:194(_construct_scopes)
       79    0.154    0.002   11.167    0.141 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\build_scopes.py:29(build_scope_graph)
    14220    0.550    0.000    7.636    0.001 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:117(insert_ref)
   654741    0.909    0.000    6.070    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:311(get_node)
1393301/738560    0.447    0.000    4.792    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\pydantic\main.py:183(__init__)
1393301/738560    3.101    0.000    4.553    0.000 {method 'validate_python' of 'pydantic_core._pydantic_core.SchemaValidator' objects}
      158    0.008    0.000    3.703    0.023 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\languages\python\python.py:8(_build_query)
      158    3.511    0.022    3.511    0.022 {method 'query' of 'tree_sitter.Language' objects}
        1    0.004    0.004    3.085    3.085 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\file_resolution\file_graph.py:42(_build_graph)
       79    0.024    0.000    3.034    0.038 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\file_resolution\file_graph.py:54(_build_file_connections)
   695291    0.456    0.000    2.940    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\utils.py:23(__init__)
      148    0.008    0.000    2.309    0.016 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\repo_resolution\repo_graph.py:208(_construct_import)
      517    0.141    0.000    2.233    0.004 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\repo_resolution\imports.py:46(import_stmt_to_import)
       79    0.028    0.000    1.913    0.024 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\capture_refs.py:10(capture_refs)
    35648    0.029    0.000    1.016    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:263(scope_by_range)
    35648    0.101    0.000    0.987    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\interval_tree.py:32(contains)
  2606802    0.647    0.000    0.945    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\networkx\classes\reportviews.py:873(<genexpr>)
    19264    0.090    0.000    0.814    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:298(add_node)
    41875    0.302    0.000    0.746    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:140(<listcomp>)
    35648    0.118    0.000    0.744    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\intervaltree\intervaltree.py:1027(__getitem__)
    41875    0.312    0.000    0.690    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:127(<listcomp>)
    58366    0.059    0.000    0.658    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\pydantic\main.py:1076(dict)
    35648    0.092    0.000    0.626    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\intervaltree\intervaltree.py:837(overlap)
      357    0.075    0.000    0.618    0.002 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:251(is_call_ref)
   162524    0.120    0.000    0.530    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\networkx\classes\reportviews.py:1093(__call__)
     5394    0.015    0.000    0.478    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:69(insert_local_def)
   162524    0.201    0.000    0.410    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\networkx\classes\reportviews.py:762(__init__)
     2163    0.204    0.000    0.376    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:163(insert_local_call)
   657925    0.254    0.000    0.374    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\networkx\classes\reportviews.py:205(__call__)
214644/44222    0.228    0.000    0.356    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\intervaltree\node.py:309(search_point)
    56095    0.106    0.000    0.349    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\scope.py:34(__next__)
    20323    0.028    0.000    0.326    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\rtfs\scope_resolution\graph.py:221(references_by_origin)
   654741    0.246    0.000    0.321    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\networkx\classes\reportviews.py:356(__getitem__)
    58366    0.032    0.000    0.318    0.000 C:\Users\jpeng\Documents\projects\cowboy_baseline\.venv\lib\site-packages\pydantic\main.py:326(model_dump)
    58366    0.286    0.000    0.286    0.000 {method 'to_python' of 'pydantic_core._pydantic_core.SchemaSerializer' objects}
    58366    0.168    0.000    0.281    0.000 {built-in method _warnings.warn}
  1475748    0.225    0.000    0.225    0.000 {built-in method __new__ of type object at 0x00007FFF7704C920}



Runtime of the function: 16.875032424926758 seconds
