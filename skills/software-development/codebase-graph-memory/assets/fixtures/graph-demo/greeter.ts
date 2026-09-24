export function greeting(name: string): string {
  return `Hello, ${name}`;
}

export function greetTeam(): string {
  return greeting("Hermes");
}
