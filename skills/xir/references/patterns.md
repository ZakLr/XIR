# Patterns

Worked end-to-end recipes. Each starts from a real question.

---

## 1. "What happens when the user clicks Archive?"

The single most important query. Do not read the component, then the handler, then
the API call, then guess. Traverse.

```bash
xir trace app.xir archiveProject
```

Read the output top to bottom: it takes a `Project`, needs `project.archive`, writes
`field.project.status`, announces `ProjectArchived`, requires confirmation, and is
exposed by `component.projectDetail.archiveButton` on the project detail surface.

Then ask what the event causes:

```bash
xir follow app.xir event.projectArchived triggers
# TRANSITION: projectArchived  [transition.projectList.populated.projectArchived]
```

That is a consequence *stated in the model*, not discovered by reading the list
component.

---

## 2. "Which actors can do X?"

```bash
xir query app.xir "who can archiveProject"
# project.archive: manager
```

Absence is meaningful: `member` is not listed, so the model says a member cannot
archive. If no actor holds the permission, the validator reports
`UNREACHABLE_CAPABILITY` — the capability is dead weight.

---

## 3. "What breaks if I rename this capability?"

Rename, and let the transaction tell you.

```bash
xir patch app.xir "patch { rename capability.archiveProject to_name: archive }"
```

The id is unchanged, so the interaction, component, invariant scope and flow all keep
pointing at it. Nothing to fix by hand.

Now change the *identity*:

```bash
xir patch app.xir "patch { rename capability.archiveProject to_id: capability.project.archive }"
```

Every reference is rewritten atomically. If any could not be, the patch rolls back
and names the offender.

---

## 4. "What is the blast radius of changing this field?"

```bash
xir query app.xir "affected field.project.status"
# AFFECTED BY status [field.project.status]
#   mutates: archiveProject  [capability.archiveProject]
```

Then widen: what uses that capability?

```bash
xir follow app.xir capability.archiveProject invokes
xir follow app.xir capability.archiveProject emits
```

Answering this by grepping the source misses references that are semantically real
but lexically invisible — a mutation reached through an interface, a state transition
driven by an event, an invariant scoped to the capability.

---

## 5. "Add a feature that makes members able to archive"

Do it in dependency order, and let validation enforce it.

```bash
xir patch app.xir "patch {
  modify actor.member permissions: permission.project.read,permission.project.create,permission.project.archive
}"
xir query app.xir "who can archiveProject"
# project.archive: member, manager
```

The model updates; the query changes. No code touched.

---

## 6. "This capability is missing a confirmation"

```bash
xir validate app.xir
# MISSING_CONFIRMATION: destructive capability deleteProject requires confirmation
```

```bash
xir patch app.xir "patch { modify capability.deleteProject confirmation: required }"
```

The validator derives "destructive" from the capability name
(`delete`/`destroy`/`archive`/`remove`/`purge`/`revoke`). If your capability is
destructive but not named that way, name it accordingly or the check will not fire.

---

## 7. "Add an error state to a screen that lacks one"

```bash
xir inspect app.xir machine.projectList
# MACHINE ... transitions: 6
```

Check whether the machine already has an error path before adding one:

```bash
xir validate app.xir
# INVALID_TRANSITION_TARGET / MISSING_INITIAL_STATE / ...
```

Then patch, adding the transition from the state that can fail:

```bash
xir patch app.xir "patch { modify machine.projectList initial: state.projectList.loading }"
```

---

## 8. "This screen looks like it has a dead state"

```bash
xir validate app.xir
# UNREACHABLE_STATE: state archived is unreachable from projectList
```

Often true and worth knowing: the state exists in the UI but nothing transitions into
it. Either add the transition or remove the state.

---

## 9. "Where do I start reading this unfamiliar model?"

Escalate deliberately:

```bash
xir parse app.xir --level 0     # what is this product
xir parse app.xir --level 1     # domain + who may act
xir parse app.xir --level 2     # the capabilities and flows
xir trace app.xir <the one you care about>
```

---

## 10. "Conceive a new product from scratch"

Order matters: each step is cheaper than the one after it. Declare in dependency
order, because a capability can only `requires` a permission that already exists and
can only `mutates` a field that already exists.

**The order:**

```text
intent (goal, requirement/decision/inference)
  -> permission
    -> actor
      -> entity + field
        -> event
          -> capability
            -> machine (states + transitions)
              -> component
                -> interaction
                  -> surface
                    -> flow (steps + branches)
```

**The result.** A complete, valid model:

```xir
experience Shop {
  goal: "Sell goods to registered buyers."

  requirement: "Buyers must confirm checkout."
  decision: "Cart is a drawer, not a page."
  inference guestCheckout {
    claim: "Guests would convert with a guest checkout."
    confidence: tentative
    evidence { analytics.cartAbandonment }
  }

  permission order.place   { description: "Place an order." }
  permission order.cancel  { description: "Cancel an order." }

  actor buyer   { permissions { order.place order.cancel } }
  actor support { permissions { order.cancel } }

  entity Order  { id: ID  status: draft | active | archived  total: Float }
  entity Product { id: ID  name: Text  price: Float }

  event OrderPlaced
  event OrderCancelled

  capability placeOrder {
    input  { order: Order }
    output: Order
    requires: order.place
    consumes: Order
    mutates { Order.status }
    emits: OrderPlaced
    audit: required
  }

  capability cancelOrder {
    input  { order: Order }
    output: Order
    requires: order.cancel
    consumes: Order
    mutates { Order.status }
    emits: OrderCancelled
    confirmation: required
    audit: required
  }

  state checkout {
    initial: idle
    idle       { on start -> editing }
    editing    { on submit -> validating  on cancel -> idle }
    validating { on success -> confirmed  on invalid -> editing  on network -> failed }
    confirmed  { on reset -> idle }
    failed     { on retry -> editing }
  }

  interaction placeOrder {
    trigger: click
    target: component.checkout.submit
    invokes: placeOrder
  }

  component Submit {
    id: component.checkout.submit
    invokes: placeOrder
    states: checkout
  }

  surface Checkout {
    presents: Order[]
    components { Submit }
    machine: checkout
  }

  flow Checkout {
    actor: buyer
    entry { surface: surface.checkout }
    step submit {
      from: surface.checkout
      action: interaction.placeOrder
      to: state.checkout.validating
    }
    branch outcome {
      from: state.checkout.validating
      success -> entity.order
      invalid -> state.checkout.editing
      network -> state.checkout.failed
    }
  }

  invariant ordersAreNotMutableOncePlaced {
    rule: "placed orders can only be cancelled"
    scope: capability.cancelOrder
  }
}
```

**8. Verify, then compile.** Never skip this — it is cheaper than debugging a
generated app.

```bash
xir validate shop.xir
xir test shop.xir
xir compile shop.xir --target react --out src/App.jsx
```

---

## 11. "Reverse-engineer an existing app"

Provenance is the discipline that keeps this honest.

| Certainty | Write it as |
|---|---|
| You read it in the spec | `requirement:` |
| You read it in the design | `decision:` |
| You read it in the code | `observation:` with `provenance { source: code }` |
| You concluded it | `inference:` with `confidence:` and `evidence { }` |

```xir
  observation archiveIsInOverflow {
    claim: "Archive is rendered in the project overflow menu."
    provenance { source: code reference: ProjectMenu.tsx:88 confidence: confirmed }
  }
  inference archiveIsRare {
    claim: "Most projects are never archived."
    confidence: probable
    evidence { analytics.archiveUsage }
  }
```

Never write a guess as a `requirement`. The whole value of the model collapses if a
plausible guess is indistinguishable from a signed-off decision.

---

## 12. "Generate tests for this product"

```bash
xir compile app.xir --target playwright --out tests/app.spec.ts
```

You get one test per interaction, walking the chain, plus one per flow. They assert
behaviour because the model states the consequences.
