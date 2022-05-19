def load_file_to_global_context_without_imports(file_path, context, injected_mocks=[]):
    with open(file_path, "r") as file_to_be_tested:
        file_content = str("")
        for mock in injected_mocks:
            file_content = file_content + mock + "= MagicMock()\n"
        for line in file_to_be_tested.readlines():
            if not line.startswith("import") and not line.startswith("from"):
                file_content = file_content + line

    exec(file_content, context)
