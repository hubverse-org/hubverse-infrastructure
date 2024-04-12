import pulumi

class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + '_id', args.inputs]
    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}

pulumi.runtime.set_mocks(
    MyMocks(),
    preview=False,  # Sets the flag `dry_run`, which is true at runtime during a preview.
)

from hubverse_infrastructure.hubs.s3 import create_bucket

@pulumi.runtime.test
async def test_create_bucket():
    def check_tags(tags):
        assert tags is not None
        assert 'hub' in tags
    
    def check_name(name):
        assert name == 'test-hub'
    
    hub_name = 'test-hub'
    bucket = create_bucket(hub_name)
    await bucket.bucket.apply(check_name).future()
    await bucket.tags.apply(check_tags).future()


