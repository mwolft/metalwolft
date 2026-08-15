import { NextResponse } from "next/server";

const destinationPath = "/mantenimiento-acabado-rejas-metalicas";

export function GET(request: Request) {
  return NextResponse.redirect(new URL(destinationPath, request.url), 301);
}

export const HEAD = GET;
