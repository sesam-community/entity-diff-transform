# entity-diff-transform
A generic transform service that generates a stream of change entities for all properties of an entity.

Set this up as a transform and given a stream / array of entities it will consider each entity and produce a change log for any properties that have been added, removed or updated. 

The service looks at the previous version of the entity and compares all root properties to the current version. If the property is now missing or changed or added an entity representing that change is exposed. 

If the entity is marked as deleted then all properties of the previous version are exposed as being changed with the new value set to "". 


