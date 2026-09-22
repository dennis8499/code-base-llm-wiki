Feature: GitHub release automation

  Scenario: [BDD-RELEASE-001] VERSION and release tag stay aligned
    Given the repository VERSION contains 0.2.1
    When release validation checks tag v0.2.1
    Then validation succeeds
    And a mismatched tag is rejected before publishing

  Scenario: [BDD-RELEASE-002] surface packages are deterministic and isolated
    Given the repository has the selected MIT license and pinned tgrep bundle
    When the release builder creates the v0.2.1 output
    Then the output contains exactly the Codex and Copilot ZIPs, update manifest, and SHA256SUMS
    And each package contains only its selected platform adapter
    And every manifest checksum matches its generated asset

  Scenario: [BDD-RELEASE-003] a package refuses the wrong platform
    Given the framework installer receives a Copilot release package
    When it prepares files for a target repository with the Codex surface
    Then it fails before writing any target file

  @manual
  Scenario: [BDD-RELEASE-004] a pushed version tag publishes a GitHub Release
    Given commit a7d78cda61b21a4e41240253df542e090df88ec0 is merged to main
    When tag v0.2.1 is pushed to dennis8499/code-base-llm-wiki
    Then GitHub Actions creates Release v0.2.1 with generated notes
    And the release contains exactly the two surface ZIPs, update manifest, and SHA256SUMS
