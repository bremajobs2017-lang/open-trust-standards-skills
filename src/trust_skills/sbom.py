"""Offline component quality review for explicitly supported SBOM JSON editions."""

from .core import InputError, finding, object_input, report


def review(data: dict) -> dict:
    object_input(data)
    cdx = data.get("bomFormat") == "CycloneDX"
    if cdx:
        if data.get("specVersion") not in ("1.5", "1.6", "1.7"):
            raise InputError("Supported CycloneDX JSON editions: 1.5, 1.6, 1.7")
        components = data.get("components")
        name, version, identity, licenses = "name", "version", "bom-ref", "licenses"
        ref = "cyclonedx"
    elif data.get("spdxVersion") == "SPDX-2.3":
        components = data.get("packages")
        name, version, identity, licenses = "name", "versionInfo", "SPDXID", "licenseConcluded"
        ref = "spdx23"
    else:
        raise InputError(
            "Expected CycloneDX 1.5–1.7 or SPDX-2.3 JSON (2.3.1 documentation); XML and SPDX 3 are unsupported"
        )
    if not isinstance(components, list):
        raise InputError("SBOM component/package collection must be an array")
    out, normalized, seen = [], [], set()

    def visit(items):
        for item in items:
            object_input(item, "component")
            loc = f"component:{len(normalized) + 1}"
            for field in (name, version, identity, licenses):
                value = item.get(field)
                if (
                    field in (name, version, identity)
                    and value is not None
                    and not isinstance(value, str)
                ):
                    raise InputError("Component name, version, and identifier fields must be text")
                if not value or value in ("NOASSERTION", "NONE"):
                    out.append(
                        finding(
                            "SBOM_MISSING_FIELD",
                            loc,
                            f"Missing or unasserted {field}; obtain provenance evidence.",
                            ref,
                        )
                    )
            id_ = item.get(identity)
            if id_ is not None and not isinstance(id_, str):
                raise InputError("Component identifiers must be strings")
            if id_ and id_ in seen:
                out.append(
                    finding("SBOM_DUPLICATE_ID", loc, "Duplicate component identifier.", ref)
                )
            if id_:
                seen.add(id_)
            normalized.append({"name": item.get(name), "version": item.get(version), "id": id_})
            if cdx and "components" in item:
                if not isinstance(item["components"], list):
                    raise InputError("Nested components must be arrays")
                visit(item["components"])

    visit(components)
    if not normalized:
        out.append(
            finding(
                "SBOM_EMPTY", "document", "No components supplied; verify inventory scope.", ref
            )
        )
    if cdx:
        dependencies = data.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise InputError("dependencies must be an array")
        metadata = object_input(data.get("metadata", {}), "metadata")
        root = object_input(metadata.get("component", {}), "metadata.component").get("bom-ref")
        known = seen | ({root} if isinstance(root, str) else set())
        for dependency in dependencies:
            object_input(dependency, "dependency")
            if not isinstance(dependency.get("ref"), str):
                raise InputError("Dependency ref must be text")
            targets = dependency.get("dependsOn", [])
            if not isinstance(targets, list) or not all(isinstance(x, str) for x in targets):
                raise InputError("dependsOn must be an array of strings")
            if dependency.get("ref") not in known or any(t not in known for t in targets):
                out.append(
                    finding(
                        "SBOM_DANGLING_REF",
                        "dependencies",
                        "Dependency graph references an unknown component.",
                        ref,
                    )
                )
    return report(
        "dependency-sbom-review",
        out,
        {"format": "CycloneDX" if cdx else "SPDX", "components": normalized},
        [
            "Component quality checks, not full schema or license-expression validation.",
            "No vulnerability feed, exploitability analysis, dependency resolution, or completeness attestation; no network access.",
        ],
    )
