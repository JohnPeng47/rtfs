from rtfs.build_scopes import build_scope_graph

DOTTED_REFERENCE = """
repo = get_or_raise(
    db_session=db_session, curr_user=current_user, repo_name=request.repo_name
)
src_repo = SourceRepo(Path(repo.source_folder))
tm_models = select_tms(
    db_session=db_session, repo_id=repo.id, request=request, src_repo=src_repo
)
"""
sg = build_scope_graph(DOTTED_REFERENCE.encode("utf-8"))
print(sg.to_str())
