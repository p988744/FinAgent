"""Reporter agent for the Plan-and-Execute agent flow."""

# Note: In this simplified design, the Replanner can directly produce the final response.
# However, for a more robust system, we might want a dedicated Reporter to synthesize a nice report.
# Since the Replanner output already has a 'response' field, we can use that or have a dedicated step.
# For this implementation, we will use the Replanner's response directly, but we keep this file
# in case we want to add a dedicated formatting/citation step later.

# Currently unused, but good for future extension.
class ReporterAgent:
    pass
