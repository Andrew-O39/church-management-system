import { redirect } from "next/navigation";

/** Parish self-view was removed from product UX; send users to their app profile. */
export default function MembersMeRedirectPage() {
  redirect("/profile");
}
