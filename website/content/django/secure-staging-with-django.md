Title: Automate and secure Django staging sites
Date: 2026-01-14 10:00
Modified: 2026-01-14 10:00
Category: Django
Tags: django, staging, security, fly.io, neon, django-lockdown, github-actions
Slug: automate-secure-django-staging
Authors: Sean Reed
lang: eng
Summary: Guide to automating and securing Django staging sites using GitHub Actions, Neon database branching, and django-lockdown. 

One of the challenges with developing web apps is ensuring bugs are caught before reaching your users. Often it is not possible to perfectly replicate the production environment that runs in the cloud on your developer machine. That means you can't be sure the code will work correctly when pushed to production, even if it passes all tests and seems fine locally, as the differences might be hiding bugs. Ideally, you want the ability to preview your changes in as realistic a setting as possible before they reach your users. When developing new features, you also want an easy way to share a preview with others for review and feedback. In this post I'll show you how you can set up automated, secure staging sites for your Django app using GitHub Actions, Neon database branching, and django-lockdown.

### Staging sites
This is where a staging site comes in. A staging site is a version of your site available in the cloud that mirrors production as closely as possible. It should match the production deployment environment, the production data, and so on. You want to make the creation of a staging site simple and fast so that it becomes a natural part of the development process, spinning one up for any pull request where a live preview is relevant before it is merged. You also want to keep your staging sites private and secure by limiting access to only those that need it. Three tools/services come in handy here for Django sites: GitHub Actions for automating the deployment, Neon database branching and masking (assuming you are using Postgres) for replicating production data, and django-lockdown for ensuring privacy and security.

### Automating staging site deployment

Let's assume your project follows the common development practice where your main branch represents your live production site and development is done on feature branches that are reviewed and merged into main via pull requests, with the updated site automatically deployed via a GitHub action. I use GitHub as the example here as it's the most popular development platform but of course the same applies with others like Gitlab. A nice workflow that works well is to have the staging site launched whenever a "PR preview app" (or similar) label is added to a pull request. The actual action performed should replicate your normal deployment script for the live site on main, but you will usually want a pared down scaling and perhaps omit certain worker processes to keep staging deployments cheap and fast. If you use the [fly.io platform](https://fly.io), they have a GitHub action that does this for you, called [fly-pr-review-apps](https://github.com/superfly/fly-pr-review-apps):

    :::yaml
    name: Staging App
    on:
      pull_request:
        types: [labeled, opened, reopened, synchronize, closed]

    env:
      FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

    jobs:
      deploy:
        if: |
          contains(github.event.pull_request.labels.*.name, 'PR preview app') &&
          github.event.action != 'closed'
        runs-on: ubuntu-latest

        concurrency:
          group: pr-${{ github.event.number }}

        environment:
          name: pr-${{ github.event.number }}
          url: ${{ steps.deploy.outputs.url }}

        steps:
          - uses: actions/checkout@v6

          - name: Deploy
            id: deploy
            uses: superfly/fly-pr-review-apps@1.5.0

      cleanup:
        if: |
          contains(github.event.pull_request.labels.*.name, 'PR preview app') &&
          github.event.action == 'closed'
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6

          - name: Destroy Fly app
            uses: superfly/fly-pr-review-apps@1.5.0

The workflow is configured to only run when a pull request has the "PR preview app" label. This means you can choose which PRs get a staging site rather than deploying one for every pull request. To use this, create a label called "PR preview app" in your repository (under Settings > Labels, or via the Labels section in any issue or PR). When you add this label to a PR, the workflow deploys the site to a unique URL based on the PR number, e.g. `pr-42.yourapp.fly.dev`. The cleanup job automatically tears it down when the PR is merged or closed. If you use another hosting provider, you can adapt the deployment and cleanup steps to use their CLI or API instead.

By using this approach you can ensure that the staging site environment is as close to production as possible. Next we will tackle how to set up the staging database to closely match production data.

### Staging site data

The basic example above will deploy the site and you could have it create a fresh database instance, run migrations, add some seed data etc. However, that would likely not be representative of the production data (and would need to be kept up to date over time) and would also be slow and costly. If you are using [Neon](https://neon.tech/) as your Postgres database provider, you can take advantage of their branching and data masking features to create a staging database that is a branch of your production database. This means it will have the same schema and data as production at the time of branching, but changes made to the staging database won't affect production. You can also apply data masking policies to obfuscate sensitive data, ensuring that any personal or confidential information is not exposed in the staging environment. It's also essentially free as no additional data storage is needed due to the way Neon implements branching using [copy-on-write storage](https://neon.com/blog/instantly-copy-tb-size-datasets-the-magic-of-copy-on-write) and scales to zero. By creating a new database branch for each PR, you can test changes to the database schema or data in isolation without affecting other staging sites or production.

Neon provides official GitHub Actions to automate this workflow: [create-branch-action](https://github.com/neondatabase/create-branch-action) for provisioning branches and [delete-branch-action](https://github.com/neondatabase/delete-branch-action) for cleanup.

Here's the deployment workflow from the previous section, enhanced with Neon database branching. The key additions are the `Create Neon Branch` step before deployment and the `Delete Neon Branch` step in cleanup:

    :::yaml
    name: Staging App
    on:
      pull_request:
        types: [labeled, opened, reopened, synchronize, closed]

    env:
      FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

    jobs:
      deploy:
        if: |
          contains(github.event.pull_request.labels.*.name, 'PR preview app') &&
          github.event.action != 'closed'
        runs-on: ubuntu-latest

        concurrency:
          group: pr-${{ github.event.number }}

        environment:
          name: pr-${{ github.event.number }}
          url: ${{ steps.deploy.outputs.url }}

        steps:
          - name: Create Neon Branch
            id: create-branch
            uses: neondatabase/create-branch-action@v6
            with:
              project_id: ${{ vars.NEON_PROJECT_ID }}
              branch_name: pr-${{ github.event.number }}
              api_key: ${{ secrets.NEON_API_KEY }}
              parent_branch: main

          - uses: actions/checkout@v6

          - name: Deploy
            id: deploy
            uses: superfly/fly-pr-review-apps@1.5.0
            with:
              secrets: DATABASE_URL=${{ steps.create-branch.outputs.db_url }}

      cleanup:
        if: |
          contains(github.event.pull_request.labels.*.name, 'PR preview app') &&
          github.event.action == 'closed'
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6

          - name: Destroy Fly app
            uses: superfly/fly-pr-review-apps@1.5.0

          - name: Delete Neon Branch
            uses: neondatabase/delete-branch-action@v3
            with:
              project_id: ${{ vars.NEON_PROJECT_ID }}
              branch: pr-${{ github.event.number }}
              api_key: ${{ secrets.NEON_API_KEY }}

The `create-branch-action` outputs a `db_url` connection string that you can pass directly to your Django app as the `DATABASE_URL` environment variable (using a package like [dj-database-url](https://github.com/jazzband/dj-database-url) to parse it in your settings). When the PR is closed or merged, the `delete-branch-action` cleans up the staging database branch automatically.

**Important**: The Neon branch creation and deployment steps must be in the same job. GitHub Actions masks outputs containing secrets (like database passwords) when passing them between jobs, which would result in an empty `DATABASE_URL`. By keeping both steps in a single job, the `db_url` can be referenced directly as a step output.

To use these actions, you'll need to set up authentication by adding your `NEON_API_KEY` as a repository secret (ideally a project scoped API key) and `NEON_PROJECT_ID` as a repository variable (in your repository's Settings > Secrets and variables > Actions). You can find these in the [Neon Console](https://console.neon.tech/) for your project. Alternatively, if you enable the [Neon GitHub Integration](https://neon.com/docs/guides/github-integration), it will automatically configure both for you. You can read more on branching in [Neon's guide](https://neon.com/blog/practical-guide-to-database-branching).

Now we have automated deployment of staging sites with realistic data that closely mirrors production. The final step is to ensure these staging sites are secure and private.

### Securing staging sites
By default, your staging sites will be publicly accessible on the internet, which may not be desirable. Whilst the URL is unique to each PR, if you follow the approach above it follows a predictable pattern and, in any case, relying on security by obscurity is rarely a good idea. To secure the site behind a password you can use the [django-lockdown](https://github.com/andrewschoen/django-lockdown) package.

First, install django-lockdown and add it to your Django configuration. In your `settings.py`:

    :::python
    import os

    INSTALLED_APPS = [
        "lockdown",
        ...
    ]

    MIDDLEWARE = [
        "lockdown.middleware.LockdownMiddleware",
        ...
    ]

    # Only enable lockdown when STAGING_PASSWORD is set
    STAGING_PASSWORD = os.environ.get("STAGING_PASSWORD")
    LOCKDOWN_ENABLED = STAGING_PASSWORD is not None
    LOCKDOWN_PASSWORDS = (STAGING_PASSWORD,) if STAGING_PASSWORD else ()

The key here is that `LOCKDOWN_ENABLED` is only `True` when the `STAGING_PASSWORD` environment variable is present. This means lockdown will be active on your staging sites (where you set the variable) but not on production or local development (where you don't). When a user visits a locked-down staging site, they'll be prompted for the password before they can access any page.

The simplest approach is to use a fixed password stored as a GitHub secret. Add a `STAGING_PASSWORD` secret to your repository (under Settings > Secrets and variables > Actions), then reference it in your deployment workflow:

    :::yaml
    - name: Deploy
      id: deploy
      uses: superfly/fly-pr-review-apps@1.5.0
      with:
        secrets: |
          DATABASE_URL=${{ steps.create-branch.outputs.db_url }}
          STAGING_PASSWORD=${{ secrets.STAGING_PASSWORD }}

This provides a simple but effective layer of security for your staging environments. You will need to manually rotate the password if someone leaves the team.

For teams requiring stricter access control, you could generate unique passwords per PR and store them in a secrets manager like [HashiCorp Vault](https://developer.hashicorp.com/vault). This ensures access to one staging site doesn't grant access to others, and passwords can be automatically rotated with each deployment.

### Conclusion

By using GitHub Actions with Fly.io's deployment, Neon's database branching, and django-lockdown, you can fully automate secure staging sites for your Django app that closely mirror production. Each pull request gets its own isolated environment with realistic data, protected behind a password, just by adding a 'PR preview app' label. When the PR is merged or closed, everything is automatically cleaned up. This workflow makes it easy to catch environment-specific bugs before they reach your users and provides a convenient way to share live previews with reviewers.