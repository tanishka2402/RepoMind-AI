from security.scanner import scan_repository


def test_detects_dynamic_execution():
    result = scan_repository({
        "files": [{
            "path": "src/app.py",
            "content": 'import os\nos.system("rm -rf /tmp/demo")\n',
        }]
    })

    assert result["status"] == "completed"
    assert result["files_scanned"] == 1
    assert any(
        finding["rule_id"] == "EXEC002"
        for finding in result["findings"]
    )


def test_detects_unsafe_yaml_load():
    result = scan_repository({
        "files": [{
            "path": "config.py",
            "content": "data = yaml.load(user_input)\n",
        }]
    })

    assert any(
        finding["rule_id"] == "DESERIALIZE001"
        for finding in result["findings"]
    )


def test_reports_empty_repository_without_claiming_safety():
    result = scan_repository({"files": []})

    assert result["status"] == "no_source_files"
    assert result["files_scanned"] == 0
    assert result["findings"] == []


def test_ignores_dependency_and_build_directories():
    result = scan_repository({
        "files": [
            {
                "path": "node_modules/example/app.js",
                "content": 'eval("something")',
            },
            {
                "path": "src/app.js",
                "content": 'console.log("hello")',
            },
        ]
    })

    assert result["files_scanned"] == 1
    assert result["findings"] == []

