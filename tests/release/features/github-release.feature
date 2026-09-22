Feature: GitHub release automation

  Scenario: [BDD-RELEASE-001] VERSION and release tag stay aligned
    Given the repository VERSION contains 0.2.0
    When release validation checks tag v0.2.0
    Then validation succeeds
    And a mismatched tag is rejected before publishing

  Scenario: [BDD-RELEASE-002] release assets are deterministic and complete
    Given the repository has the selected MIT license and pinned tgrep bundle
    When the release builder creates the v0.2.0 output
    Then the output contains exactly the two archives, update manifest, and SHA256SUMS
    And every manifest checksum matches its generated asset

  Scenario: [BDD-RELEASE-003] framework release automation stays out of targets
    Given the framework installer selects the Copilot surface
    When it prepares files for a target repository
    Then .github/workflows/release.yml is not selected for installation

  @manual
  Scenario: [BDD-RELEASE-004] a pushed version tag publishes a GitHub Release
    Given commit a7d78cda61b21a4e41240253df542e090df88ec0 is merged to main
    When tag v0.2.0 is pushed to dennis8499/code-base-llm-wiki
    Then GitHub Actions creates Release v0.2.0 with generated notes
    And the release contains exactly the four documented assets
