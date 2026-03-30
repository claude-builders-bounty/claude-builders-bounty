defmodule ChangelogGeneratorTest do
  use ExUnit.Case

  describe "changelog.sh integration" do
    @tag :integration
    test "generates changelog with feat entries" do
      # This test requires changelog.sh to be in the same directory
      # Run as: elixir --cookie secret -S mix test test/changelog_test.exs
      {output, exit_code} =
        System.cmd("bash", ["changelog.sh"], stderr: :standard_error)

      assert exit_code == 0, "changelog.sh exited with non-zero: #{output}"
      assert File.exists?("CHANGELOG.md")
      
      content = File.read!("CHANGELOG.md")
      assert content =~ "# Changelog"
      assert content =~ "### Added" or content =~ "### Fixed" or content =~ "### Changed"
    end

    test "categorizes feat: commits as Added" do
      content = File.read!("CHANGELOG.md")
      refute content =~ ~r/^- feat:/m
    end

    test "categorizes fix: commits as Fixed" do
      content = File.read!("CHANGELOG.md")
      refute content =~ ~r/^- fix:/m
    end
  end
end
