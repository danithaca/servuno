Feature: Test manage personal feature

  @core
  Scenario: basic manage interface is there
    Given I am logged in as user "test@servuno.com" with password "password"
    And I am on "/circle/manage/personal"
    Then the response status code should be 200
    And I should see "Manage"
    And I should see a "#new-contact" element
    And I should see a "#new-contact-add-btn" element

  @javascript @core
  Scenario: add and remove UI, does not submit
    Given I am logged in as user "test@servuno.com" with password "password"
    And I am on "/circle/manage/personal"

    When I run the following Javascript:
      """
      $('li[data-email="test1@servuno.com"] i.fa-remove').click();
      """
    Then I should not see "test1@servuno.com"

    When I run the following Javascript:
      """
      $('li[data-email="test2@servuno.com"] i.fa-remove').click();
      """
    Then I should not see "test2@servuno.com"

    When I fill in "new-contact" with "test1@servuno.com test2@servuno.com"
    And I press "new-contact-add-btn"
    Then I should see "test1@servuno.com"
    And I should see "test2@servuno.com"